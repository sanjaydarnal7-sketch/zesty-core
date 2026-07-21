"""
Base Provider Interface
Production interface for all LLM providers used by Zesty OS.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """
    Every provider must implement this interface.
    """

    name: str = "base"

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> str:
        """
        Generate a response from the provider.
        """
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """
        Returns True if the provider is ready for inference.
        """
        raise NotImplementedError
