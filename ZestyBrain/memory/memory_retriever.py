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

    def context(self, limit: int = 8) -> str:

        messages = self.conversation(limit)

        if not messages:
            return ""

        cleaned = []

        seen = set()

        for message in messages:

            message = message.strip()

            if not message:
                continue

            if message in seen:
                continue

            seen.add(message)
            cleaned.append(message)

        if not cleaned:
            return ""

        return "\n".join(cleaned)
