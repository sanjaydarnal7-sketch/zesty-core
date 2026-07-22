"""
Zesty Fact Store

Thread-safe persistent storage for structured facts.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


class FactStore:

    def __init__(self, db_path: str = "zesty_memory.db"):

        self.path = Path(db_path)

        self._create()

    def _connect(self):

        return sqlite3.connect(self.path)

    def _create(self):

        with self._connect() as conn:

            conn.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                UNIQUE(category, key, value)
            )
            """)

            conn.commit()

    def remember(
        self,
        category: str,
        key: str,
        value: str,
    ):

        with self._connect() as conn:

            conn.execute(
                """
                INSERT OR IGNORE INTO facts
                (category,key,value)
                VALUES (?,?,?)
                """,
                (
                    category,
                    key,
                    value,
                ),
            )

            conn.commit()

    def load(self):

        with self._connect() as conn:

            cursor = conn.execute(
                """
                SELECT category,key,value
                FROM facts
                ORDER BY
                    category,
                    key,
                    rowid
                """
            )

            return cursor.fetchall()

    def clear(self):

        with self._connect() as conn:

            conn.execute(
                "DELETE FROM facts"
            )

            conn.commit()


    def exists(
        self,
        category: str,
        key: str,
        value: str,
    ) -> bool:

        with self._connect() as conn:

            cursor = conn.execute(
                """
                SELECT 1
                FROM facts
                WHERE category=?
                  AND key=?
                  AND value=?
                LIMIT 1
                """,
                (
                    category,
                    key,
                    value,
                ),
            )

            return cursor.fetchone() is not None
