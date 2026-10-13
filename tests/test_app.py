import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.knowledge import split_text
from app.main import create_app
from app.model import Model, TicketCreate, NoEvidenceError


class SupportFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = Settings(_env_file=None, api_keys="test-owner-a-123456789,test-owner-b-123456789",
                                 db_path=Path(self.temp.name)/"test.sqlite3",
                                 model_mode="offline", retrieval_mode="lexical", knowledge_source="faq")
        self.app = create_app(self.settings)
        self.client = TestClient(self.app).__enter__()
        self.a = {"X-API-Key": "test-owner-a-123456789"}
        self.b = {"X-API-Key": "test-owner-b-123456789"}
        self.session = self.client.post("/sessions", headers=self.a).json()["session_id"]

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.temp.cleanup()

    def chat(self, text, request_id=None, headers=None, session=None):
        return self.client.post("/chat", headers=headers or self.a, json={
            "session_id": session or self.session, "message": text,
            "request_id": request_id or str(uuid4())})

    def create_ticket(self):
        preview = self.chat("创建工单：付款后订单状态没有更新").json()
        self.assertTrue(preview["needs_confirmation"])
        self.assertEqual(self.client.get("/tickets", headers=self.a).json(), [])
        result = self.chat("确认提交")
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()["ticket"]["id"]

    def test_auth_and_empty_input(self):
        self.assertEqual(self.client.post("/sessions").status_code, 401)
        self.assertEqual(self.chat("   ").status_code, 422)
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_faq_returns_evidence_and_graph_trace(self):
        r = self.chat("忘记密码怎么重置？").json()
        self.assertIn("faq-password", [s["id"] for s in r["sources"]])
        self.assertEqual(r["trace"], ["classify", "retrieve", "respond"])
        self.assertIn("密码", r["reply"])

    def test_unknown_allows_two_clarifications_then_handoff(self):
        self.assertEqual(self.chat("嗯嗯啊啊").json()["clarifications"], 1)
        self.assertEqual(self.chat("还是那样").json()["clarifications"], 2)
        r = self.chat("就那个事情").json()
        self.assertEqual(r["status"], "handoff_pending")
        self.assertEqual(r["handoff_reason"], "max_clarification")
        self.assertEqual(len(self.client.get("/handoffs", headers=self.a).json()), 1)
        self.assertEqual(self.chat("你好").status_code, 409)

    def test_complaints_bypass_retrieval(self):
        r = self.chat("我要投诉").json()
        self.assertEqual(r["trace"], ["classify", "handoff"])
        self.assertEqual(r["status"], "handoff_pending")

    def test_explicit_human_request(self):
        r = self.chat("转人工").json()
        self.assertEqual(r["intent"], "human_request")
        self.assertEqual(r["status"], "handoff_pending")

    def test_no_knowledge_handoff(self):
        with patch.object(self.app.state.knowledge, "search", return_value=[]):
            r = self.chat("保修政策是什么").json()
        self.assertEqual(r["handoff_reason"], "no_knowledge")
        self.assertFalse(r["sources"])

    def test_tool_creation_confirmation_cancel(self):
        self.chat("创建工单：设备故障")
        self.assertFalse(self.chat("取消").json()["needs_confirmation"])
        self.assertEqual(self.client.get("/tickets", headers=self.a).json(), [])

    def test_ticket_query_and_cross_user_access(self):
        ticket = self.create_ticket()
        self.assertEqual(self.chat("查询工单" + ticket + "的状态").json()["ticket"]["id"], ticket)
        self.assertEqual(self.client.get("/tickets/"+ticket, headers=self.b).status_code, 404)
        self.assertEqual(self.client.get("/sessions/"+self.session, headers=self.b).status_code, 404)
        self.assertEqual(self.chat("你好", headers=self.b).status_code, 404)
        other_session = self.client.post("/sessions", headers=self.b).json()["session_id"]
        r = self.chat("查询 " + ticket, headers=self.b, session=other_session).json()
        self.assertIsNone(r["ticket"])

    def test_missing_ticket_id_does_not_guess(self):
        r = self.chat("查询工单进度").json()
        self.assertIn("提供", r["reply"])
        self.assertIsNone(r["ticket"])

    def test_duplicate_request_replays_without_duplicate_ticket(self):
        self.chat("创建工单：设备故障")
        request_id = str(uuid4())
        a = self.chat("确认提交", request_id).json()
        b = self.chat("确认提交", request_id).json()
        self.assertEqual(a, b)
        self.assertEqual(len(self.client.get("/tickets", headers=self.a).json()), 1)
        self.assertEqual(self.chat("不同消息", request_id).status_code, 409)

    def test_concurrent_duplicate_confirmation(self):
        self.chat("创建工单：设备故障")
        request_id = str(uuid4())
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: self.chat("确认提交", request_id), range(2)))
        self.assertTrue(all(r.status_code == 200 for r in responses))
        self.assertEqual(responses[0].json(), responses[1].json())
        self.assertEqual(len(self.client.get("/tickets", headers=self.a).json()), 1)

    def test_model_failure_is_handoff_not_fake_answer(self):
        with patch.object(self.app.state.model, "classify", side_effect=TimeoutError()):
            r = self.chat("退款多久到账").json()
        self.assertEqual(r["handoff_reason"], "model_failed")
        self.assertEqual(r["status"], "handoff_pending")

    def test_tool_failure_no_write(self):
        with patch.object(self.app.state.model, "plan_tool", side_effect=ValueError("bad_arguments")):
            r = self.chat("创建工单：设备故障").json()
        self.assertEqual(r["handoff_reason"], "tool_failed")
        self.assertEqual(self.client.get("/tickets", headers=self.a).json(), [])

    def test_insufficient_evidence_handoff_keeps_retrieved_sources_uncited(self):
        with patch.object(self.app.state.model, "answer_grounded", side_effect=NoEvidenceError()):
            r = self.chat("忘记密码怎么重置？").json()
        self.assertEqual(r["handoff_reason"], "insufficient_evidence")
        self.assertTrue(r["sources"])
        self.assertFalse(any(s["cited"] for s in r["sources"]))

    def test_session_persists_after_app_restart(self):
        self.chat("不明确")
        second = create_app(self.settings)
        with TestClient(second) as client:
            r = client.get("/sessions/"+self.session, headers=self.a).json()
            self.assertEqual(r["clarifications"], 1)
            self.assertEqual(len(r["messages"]), 2)

    def test_feedback_is_owned(self):
        request_id = self.chat("你好").json()["request_id"]
        body = {"request_id": request_id, "rating": 5}
        self.assertEqual(self.client.post("/feedback", headers=self.a, json=body).status_code, 200)
        self.assertEqual(self.client.post("/feedback", headers=self.b, json=body).status_code, 404)


class ModelBoundaryTests(unittest.TestCase):
    def test_splitting_preserves_overlap(self):
        self.assertEqual(split_text("abcdefgh", 5, 2), ["abcde", "defgh", "gh"])
        with self.assertRaises(ValueError):
            split_text("abc", 2, 2)

    def test_openai_compatible_response_is_validated(self):
        settings = Settings(_env_file=None, model_mode="openai", llm_api_key="test-fixture-not-a-real-key")
        model = Model(settings)
        model.client.close()
        def handler(request):
            payload = json.loads(request.content)
            self.assertEqual(payload["response_format"]["type"], "json_object")
            return httpx.Response(200, json={"choices": [{"message": {
                "content": '{"intent":"knowledge_query","confidence":0.9}'}}]})
        model.client = httpx.Client(transport=httpx.MockTransport(handler))
        self.assertEqual(model.classify("退款怎么办", []).intent, "knowledge_query")
        model.close()

    def test_unexpected_tool_and_bad_parameters_rejected(self):
        settings = Settings(_env_file=None, model_mode="openai", llm_api_key="test-fixture-not-a-real-key")
        model = Model(settings)
        model.client.close()
        model.client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200,
            json={"choices": [{"message": {"tool_calls": [{"function": {
                "name": "delete_all", "arguments": "{}"}}]}}]})))
        with self.assertRaises(ValueError):
            model.plan_tool("ticket_create", "创建工单：故障")
        with self.assertRaises(ValueError):
            TicketCreate(title="有效标题", description="说明", owner="another-user")
        model.close()


if __name__ == "__main__":
    unittest.main()
