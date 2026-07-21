"""
Provider Bootstrap
Registers all available providers.
"""

from __future__ import annotations

from .ollama_provider import OllamaProvider
from .registry import ProviderRegistry


class ProviderBootstrap:
    """
    Bootstraps the provider registry.
    """

    @staticmethod
    def initialize(registry: ProviderRegistry) -> None:
        registry.register(OllamaProvider())
