import os
import sqlite3
from typing import List, Dict, Any

class ASTIndexer:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                kind TEXT NOT NULL,
                file_path TEXT NOT NULL,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL
            )
        """)
        self.conn.commit()

    def index_file(self, file_path: str, language: str = "python"):
        if not os.path.exists(file_path):
            return
            
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM symbols WHERE file_path = ?", (file_path,))
            
            for idx, line in enumerate(lines):
                line_str = line.strip()
                if line_str.startswith("def ") or line_str.startswith("class "):
                    parts = line_str.split()
                    if len(parts) > 1:
                        sym_name = parts[1].split("(")[0].split(":")[0]
                        kind = "function" if line_str.startswith("def ") else "class"
                        cursor.execute(
                            "INSERT INTO symbols (name, kind, file_path, start_line, end_line) VALUES (?, ?, ?, ?, ?)",
                            (sym_name, kind, file_path, idx + 1, idx + 1)
                        )
            self.conn.commit()
        except Exception:
            pass

    def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name, kind, file_path, start_line, end_line FROM symbols WHERE name LIKE ?",
            (f"%{query}%",)
        )
        rows = cursor.fetchall()
        return [
            {
                "name": r[0],
                "kind": r[1],
                "file_path": r[2],
                "start_line": r[3],
                "end_line": r[4]
            }
            for r in rows
        ]
