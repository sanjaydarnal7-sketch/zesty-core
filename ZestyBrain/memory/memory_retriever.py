"""
Zesty Memory Retriever

Provides conversation history for prompts.
"""

from __future__ import annotations

from ZestyBrain.memory.memory_store import MemoryStore


class MemoryRetriever:

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def conversation(self, limit: int = 5) -> list[str]:
        return self.store.recent(limit)

    def context(self, limit: int = 5) -> str:

        messages = self.conversation(limit)

        if not messages:
            return ""

        lines = ["RECENT CONVERSATION"]

        for i, message in enumerate(messages, start=1):
            lines.append(f"{i}. {message}")

        return "\n".join(lines)
