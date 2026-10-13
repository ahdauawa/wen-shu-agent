import hashlib
import json
import logging
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import Settings
from app.engine import build_graph
from app.knowledge import Knowledge
from app.model import Model
from app.store import Store

logger = logging.getLogger("wenshu")


class ChatRequest(BaseModel):
    session_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    request_id: UUID
    message: str = Field(min_length=1, max_length=1500)


class FeedbackRequest(BaseModel):
    request_id: UUID
    rating: int = Field(ge=1, le=5)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    if not settings.keys or any(len(key) < 16 or key == "replace-with-a-random-local-key" for key in settings.keys):
        raise RuntimeError("请在 .env 设置至少 16 位随机 WENSHU_API_KEYS；参见 README。")
    store = Store(settings.db_path)
    model = Model(settings)
    knowledge = Knowledge(settings)
    rate = defaultdict(deque)
    rate_lock = Lock()

    @asynccontextmanager
    async def lifespan(_):
        yield
        model.close()

    app = FastAPI(title="问枢 · 客服分流与工单助手", version="0.1.0", lifespan=lifespan)
    app.state.model = model
    app.state.knowledge = knowledge
    app.state.store = store

    def authenticate(x_api_key: Annotated[str | None, Header()] = None) -> str:
        if not x_api_key or not any(secrets.compare_digest(x_api_key, key) for key in settings.keys):
            raise HTTPException(401, "无效 API Key")
        owner = hashlib.sha256(x_api_key.encode()).hexdigest()
        with rate_lock:
            window = rate[owner]
            current = time.monotonic()
            while window and window[0] < current-60:
                window.popleft()
            if len(window) >= 120:
                raise HTTPException(429, "请求过于频繁，请稍后重试")
            window.append(current)
        return owner

    User = Annotated[str, Depends(authenticate)]

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    @app.get("/health")
    def health():
        return {"status": "ok", "model_mode": settings.model_mode,
                "retrieval_mode": settings.retrieval_mode, "faq_count": len(knowledge.faq)}

    @app.post("/sessions", status_code=201)
    def new_session(owner: User):
        return {"session_id": store.create_session(owner)}

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str, owner: User):
        with store.connect() as db:
            state = store.session(db, owner, session_id)
        if state is None:
            raise HTTPException(404, "会话不存在")
        return {"session_id": session_id, **state}

    @app.get("/tickets")
    def list_tickets(owner: User):
        with store.connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT id,title,status,created_at FROM tickets WHERE owner=? ORDER BY created_at DESC LIMIT 100", (owner,))]

    @app.get("/tickets/{ticket_id}")
    def get_ticket(ticket_id: str, owner: User):
        with store.connect() as db:
            ticket = store.query_ticket(db, owner, ticket_id)
        if ticket is None:
            raise HTTPException(404, "工单不存在")
        return ticket

    @app.get("/handoffs")
    def list_handoffs(owner: User):
        with store.connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT id,session_id,reason,summary,created_at FROM handoffs WHERE owner=? ORDER BY created_at DESC LIMIT 100", (owner,))]

    @app.post("/feedback")
    def feedback(body: FeedbackRequest, owner: User):
        with store.connect() as db:
            exists = db.execute("SELECT 1 FROM requests WHERE owner=? AND request_id=?",
                                (owner, str(body.request_id))).fetchone()
            if not exists:
                raise HTTPException(404, "对话请求不存在")
            db.execute("INSERT INTO feedback VALUES (?,?,?) ON CONFLICT(owner,request_id) DO UPDATE SET rating=excluded.rating",
                       (owner, str(body.request_id), body.rating))
        return {"saved": True}

    @app.post("/chat")
    def chat(body: ChatRequest, owner: User):
        text = body.message.strip()
        if not text:
            raise HTTPException(422, "消息不能为空")
        request_id = str(body.request_id)
        fingerprint = hashlib.sha256(json.dumps([body.session_id, text], ensure_ascii=False).encode()).hexdigest()
        started = time.perf_counter()
        try:
            with store.connect() as db:
                # ponytail: one SQLite writer serializes chats, including model latency.
                # For concurrent production traffic use per-session coordination and an outbox.
                db.execute("BEGIN IMMEDIATE")
                cached = db.execute("SELECT fingerprint,response FROM requests WHERE owner=? AND request_id=?",
                                    (owner, request_id)).fetchone()
                if cached:
                    if cached["fingerprint"] != fingerprint:
                        raise HTTPException(409, "request_id 已用于不同请求")
                    return json.loads(cached["response"])
                state = store.session(db, owner, body.session_id)
                if state is None:
                    raise HTTPException(404, "会话不存在")
                if state["status"] == "handoff_pending":
                    raise HTTPException(409, "此会话已转人工，请创建新会话")
                result = build_graph(settings, model, knowledge, store, db, owner, body.session_id).invoke({
                    "text": text, "history": state["messages"],
                    "clarifications": state["clarifications"], "pending_ticket": state.get("pending_ticket"),
                    "status": "active", "reply": "", "reason": "", "evidence": [],
                    "tool": None, "ticket": None, "handoff_id": None, "trace": [],
                }, {"recursion_limit": 12})
                if result["intent"] != "unknown" and result["confidence"] >= settings.intent_threshold:
                    result["clarifications"] = 0
                updated = {"messages": (state["messages"] + [{"role": "user", "content": text},
                    {"role": "assistant", "content": result["reply"]}])[-24:],
                    "clarifications": result["clarifications"], "status": result["status"],
                    "pending_ticket": result.get("pending_ticket")}
                store.save_session(db, owner, body.session_id, updated)
                response = {"request_id": request_id, "session_id": body.session_id,
                    **{k: result.get(k) for k in ("reply", "intent", "confidence", "status", "tool", "ticket", "handoff_id", "trace")},
                    "clarifications": updated["clarifications"], "needs_confirmation": bool(updated["pending_ticket"]),
                    "sources": [{"id": d["id"], "source": d["source"], "score": d["score"]} for d in result["evidence"]],
                    "handoff_reason": result.get("reason"), "model_mode": settings.model_mode,
                    "retrieval_mode": settings.retrieval_mode,
                    "elapsed_ms": round((time.perf_counter()-started)*1000, 2)}
                db.execute("INSERT INTO requests VALUES(?,?,?,?)",
                           (owner, request_id, fingerprint, json.dumps(response, ensure_ascii=False)))
        except sqlite3.OperationalError:
            raise HTTPException(503, "存储暂时繁忙，请使用同一 request_id 重试") from None
        logger.info(json.dumps({"event": "chat_completed", "request_id": request_id,
            "intent": response["intent"], "status": response["status"],
            "elapsed_ms": response["elapsed_ms"], "model_mode": settings.model_mode}))
        return response

    return app
