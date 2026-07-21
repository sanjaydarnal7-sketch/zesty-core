"""
Zesty Memory Store

A simple in-memory storage backend.
This can later be replaced with ChromaDB,
SQLite, PostgreSQL or any vector database.
"""

from __future__ import annotations

from typing import List


class MemoryStore:

    def __init__(self) -> None:
        self._messages: List[str] = []

    def add(self, message: str) -> None:
        if message.strip():
            self._messages.append(message.strip())

    def recent(self, limit: int = 10) -> List[str]:
        return self._messages[-limit:]

    def clear(self) -> None:
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)
