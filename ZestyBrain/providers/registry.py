"""
Provider Registry
Registers and retrieves LLM providers.
"""

from __future__ import annotations

from typing import Dict

from .base_provider import BaseProvider


class ProviderRegistry:
    """
    Registry for all available providers.
    """

    def __init__(self) -> None:
        self._providers: Dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> BaseProvider | None:
        return self._providers.get(name)

    def all(self) -> dict[str, BaseProvider]:
        return dict(self._providers)

    def available(self) -> list[str]:
        return sorted(self._providers.keys())

    def has(self, name: str) -> bool:
        return name in self._providers
