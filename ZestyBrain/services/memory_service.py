"""
Memory Service
"""

from __future__ import annotations

from ..memory.memory_engine import MemoryEngine
from ..memory.memory_pipeline import MemoryPipeline
from ..memory.fact_memory import FactMemory


class MemoryService:
    """
    High-level interface for Zesty memory operations.
    """

    def __init__(
        self,
        memory: MemoryEngine | None = None,
        facts: FactMemory | None = None,
    ):
        self.memory = memory or MemoryEngine()
        self.facts = facts or FactMemory()

        self.pipeline = MemoryPipeline(
            memory=self.memory,
            facts=self.facts,
        )

    def remember(self, text: str) -> None:
        self.memory.remember(text)
        self.pipeline.process(text)

    def learn(self, text: str) -> None:
        self.pipeline.process(text)

    def context(self) -> str:
        context = self.memory.context()

        fact_context = self.facts.prompt_context()

        if fact_context.strip():
            if context.strip():
                context += "\n\n"
            context += fact_context

        return context

    def messages(self):
        return self.memory.messages()

    def clear(self):
        if hasattr(self.memory, "clear"):
            self.memory.clear()

    def facts_context(self) -> str:
        return self.facts.prompt_context()
