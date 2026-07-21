"""
SQLite Memory Store

Thread-safe persistent conversation storage.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


class SQLiteMemoryStore:

    def __init__(self, db_path: str = "zesty.db") -> None:
        self.path = Path(db_path)
        self._create()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _create(self) -> None:

        with self._connect() as conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    def add(self, role: str, content: str) -> None:

        with self._connect() as conn:

            conn.execute(
                "INSERT INTO memories(role, content) VALUES(?, ?)",
                (role, content),
            )

            conn.commit()

    def recent(self, limit: int = 20):

        with self._connect() as conn:

            cur = conn.execute(
                """
                SELECT role, content
                FROM memories
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )

            return list(reversed(cur.fetchall()))

    def clear(self) -> None:

        with self._connect() as conn:

            conn.execute("DELETE FROM memories")

            conn.commit()
