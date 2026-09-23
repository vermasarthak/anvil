import json
import sqlite3
import time
from typing import Any, Dict, List, Optional


class SessionStore:
    def __init__(self, db_path: str = "sessions.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                model TEXT NOT NULL,
                created_at REAL NOT NULL,
                transcript TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def save_session(self, session_id: str, title: str, model: str, transcript: List[Dict[str, Any]]):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessions (id, title, model, created_at, transcript)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                transcript=excluded.transcript
            """,
            (session_id, title, model, time.time(), json.dumps(transcript)),
        )
        self.conn.commit()

    def list_sessions(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, model, created_at FROM sessions ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [{"id": r[0], "title": r[1], "model": r[2], "created_at": r[3]} for r in rows]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, model, created_at, transcript FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {"id": row[0], "title": row[1], "model": row[2], "created_at": row[3], "transcript": json.loads(row[4])}
