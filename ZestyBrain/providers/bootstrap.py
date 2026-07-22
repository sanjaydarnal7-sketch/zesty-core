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

    _initialized = False

    @staticmethod
    def initialize(registry: ProviderRegistry) -> None:

        if ProviderBootstrap._initialized:
            return

        registry.register(OllamaProvider())

        ProviderBootstrap._initialized = True
