"""
ZestyBrain Providers Package
Public provider registry and bootstrap utilities.
"""

from .base_provider import BaseProvider
from .ollama_provider import OllamaProvider
from .registry import ProviderRegistry
from .bootstrap import ProviderBootstrap

__all__ = [
    "BaseProvider",
    "OllamaProvider",
    "ProviderRegistry",
    "ProviderBootstrap",
    "create_registry",
]


__version__ = "2.0.0"


def create_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    ProviderBootstrap.initialize(registry)
    return registry
