"""
Zesty Memory Engine
"""

from __future__ import annotations

from ZestyBrain.memory.memory_store import MemoryStore
from ZestyBrain.memory.memory_retriever import MemoryRetriever
from ZestyBrain.memory.storage.sqlite_store import SQLiteMemoryStore


class MemoryEngine:

    def __init__(self) -> None:
        self.store = MemoryStore()
        self.database = SQLiteMemoryStore()
        self.retriever = MemoryRetriever(self.store)

        # Startup replay temporarily disabled while migrating persona.
        # Historical data remains in SQLite.
        pass

    def remember(self, message: str) -> None:
        self.store.add(message)

        if message.startswith("User:"):
            self.database.add("user", message[5:].strip())

        elif message.startswith("Zesty:"):
            self.database.add("assistant", message[6:].strip())

    def context(self, limit: int = 5) -> str:
        return self.retriever.context(limit)

    def messages(self, limit: int = 10) -> list[dict]:
        messages = []

        for item in self.store.recent(limit):
            if item.startswith("User:"):
                messages.append({
                    "role": "user",
                    "content": item[5:].strip(),
                })
            elif item.startswith("Zesty:"):
                messages.append({
                    "role": "assistant",
                    "content": item[6:].strip(),
                })

        return messages

    def clear(self) -> None:
        self.store.clear()
        self.database.clear()
