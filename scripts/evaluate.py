"""Reproducible offline baseline. No synthetic claims about a real LLM."""
import json
import math
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

CASES = {
    "knowledge_query": ["忘记密码怎么重置", "退款多久处理", "如何申请发票", "物流在哪里查看", "怎么取消自动续费"],
    "ticket_query": ["查询工单进度", "我的工单状态", "查一下工单", "查询 TKABC12345", "工单处理进度如何"],
    "ticket_create": ["创建工单：付款问题", "提交工单：设备异常", "新建工单：收不到邮件", "我要报修", "反馈问题：页面打不开"],
    "complaint": ["我要投诉", "服务太差", "我要举报", "你们欺骗客户", "投诉退款太慢"],
    "human_request": ["转人工", "人工客服", "帮我找人工", "我要真人客服", "转人工咨询退款"],
    "chitchat": ["你好", "您好", "谢谢", "再见", "hello"],
    "unknown": ["嗯", "那个东西", "帮一下", "弄好了没", "不太明白"],
}


def main():
    with tempfile.TemporaryDirectory() as folder:
        settings = Settings(_env_file=None, api_keys="evaluation-fixture-key-only",
                            db_path=Path(folder)/"eval.sqlite3", model_mode="offline", retrieval_mode="lexical", knowledge_source="faq")
        app = create_app(settings)
        headers = {"X-API-Key": "evaluation-fixture-key-only"}
        results, latencies = [], []
        with TestClient(app) as client:
            for expected, messages in CASES.items():
                for message in messages:
                    session = client.post("/sessions", headers=headers).json()["session_id"]
                    start = time.perf_counter()
                    response = client.post("/chat", headers=headers, json={"session_id": session,
                        "request_id": str(uuid4()), "message": message})
                    response.raise_for_status()
                    data = response.json()
                    latencies.append((time.perf_counter()-start)*1000)
                    results.append({"text": message, "expected": expected, "actual": data["intent"],
                                    "correct": expected == data["intent"]})
            retrieval = [{"id": f["id"], "hit": f["id"] in
                         [r["id"] for r in app.state.knowledge.search(f["question"], k=5)]}
                         for f in app.state.knowledge.faq]
        ordered = sorted(latencies)
        report = {"generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "offline rules + lexical retrieval", "real_model_tested": False,
            "dataset": "35 handwritten smoke cases; retrieval uses exact FAQ questions, not held-out queries",
            "sample_count": len(results), "intent_accuracy": sum(x["correct"] for x in results)/len(results),
            "retrieval_exact_question_recall_at_5": sum(x["hit"] for x in retrieval)/len(retrieval),
            "latency_ms": {"p50": ordered[len(ordered)//2], "p99": ordered[math.ceil(len(ordered)*.99)-1]},
            "cases": results, "retrieval_cases": retrieval}
    target = Path("reports/offline-evaluation.json")
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("cases", "retrieval_cases")}, ensure_ascii=False, indent=2))
    print("Report:", target)


if __name__ == "__main__":
    main()
