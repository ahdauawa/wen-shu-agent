"""SQLite stores sessions, tool effects and replayable responses in one transaction."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, state TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tickets (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, title TEXT NOT NULL,
                    description TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS handoffs (
                    id TEXT PRIMARY KEY, session_id TEXT NOT NULL UNIQUE,
                    owner TEXT NOT NULL, reason TEXT NOT NULL, summary TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS requests (
                    owner TEXT NOT NULL, request_id TEXT NOT NULL,
                    fingerprint TEXT NOT NULL, response TEXT NOT NULL,
                    PRIMARY KEY(owner, request_id)
                );
                CREATE TABLE IF NOT EXISTS feedback (
                    owner TEXT NOT NULL, request_id TEXT NOT NULL,
                    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                    PRIMARY KEY(owner, request_id)
                );
                CREATE INDEX IF NOT EXISTS tickets_owner ON tickets(owner);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def create_session(self, owner: str) -> str:
        session_id = uuid4().hex
        with self.connect() as db:
            db.execute("INSERT INTO sessions VALUES (?, ?, ?, ?)",
                       (session_id, owner, json.dumps({"messages": [], "clarifications": 0,
                        "status": "active", "pending_ticket": None}, ensure_ascii=False), now()))
        return session_id

    def session(self, db, owner: str, session_id: str) -> dict | None:
        row = db.execute("SELECT state FROM sessions WHERE id=? AND owner=?",
                         (session_id, owner)).fetchone()
        return json.loads(row["state"]) if row else None

    def save_session(self, db, owner: str, session_id: str, state: dict):
        db.execute("UPDATE sessions SET state=?, updated_at=? WHERE id=? AND owner=?",
                   (json.dumps(state, ensure_ascii=False), now(), session_id, owner))

    def create_ticket(self, db, owner: str, title: str, description: str) -> dict:
        ticket = {"id": "TK" + uuid4().hex[:16].upper(), "title": title,
                  "description": description, "status": "open", "created_at": now()}
        db.execute("INSERT INTO tickets(id,owner,title,description,status,created_at) VALUES(?,?,?,?,?,?)",
                   (ticket["id"], owner, title, description, ticket["status"], ticket["created_at"]))
        return ticket

    def query_ticket(self, db, owner: str, ticket_id: str) -> dict | None:
        row = db.execute("SELECT id,title,description,status,created_at FROM tickets WHERE id=? AND owner=?",
                         (ticket_id, owner)).fetchone()
        return dict(row) if row else None

    def handoff(self, db, owner: str, session_id: str, reason: str, summary: str) -> str:
        handoff_id = "HF" + uuid4().hex[:16].upper()
        db.execute("INSERT OR IGNORE INTO handoffs VALUES (?,?,?,?,?,?)",
                   (handoff_id, session_id, owner, reason, summary, now()))
        return db.execute("SELECT id FROM handoffs WHERE session_id=? AND owner=?",
                          (session_id, owner)).fetchone()["id"]
