import os
import sqlite3
from typing import List, Dict, Any
import tree_sitter_languages

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
            parser = tree_sitter_languages.get_parser(language)
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                code = f.read()
                
            tree = parser.parse(bytes(code, "utf-8"))
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM symbols WHERE file_path = ?", (file_path,))
            
            def traverse(node):
                if node.type in ["function_definition", "class_definition"]:
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        sym_name = code[name_node.start_byte:name_node.end_byte]
                        kind = "function" if node.type == "function_definition" else "class"
                        cursor.execute(
                            "INSERT INTO symbols (name, kind, file_path, start_line, end_line) VALUES (?, ?, ?, ?, ?)",
                            (sym_name, kind, file_path, node.start_point[0] + 1, node.end_point[0] + 1)
                        )
                for child in node.children:
                    traverse(child)

            traverse(tree.root_node)
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
