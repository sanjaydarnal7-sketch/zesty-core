"""
Conversation Service
"""

from __future__ import annotations

from ..runtime_manager import RuntimeManager


class ConversationService:
    """
    Thin service wrapper around RuntimeManager.
    """

    def __init__(self, runtime: RuntimeManager | None = None):
        self.runtime = runtime or RuntimeManager()

    def is_ready(self) -> bool:
        return self.runtime.is_ready()

    def chat(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> str:
        return self.runtime.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    def generate(self, *args, **kwargs):
        return self.chat(*args, **kwargs)
