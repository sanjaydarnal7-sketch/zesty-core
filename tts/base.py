"""TTS provider interface — swap engines without touching the router."""

from __future__ import annotations

from abc import ABC, abstractmethod


class TTSProvider(ABC):
    """Minimal contract for any TTS backend."""

    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider can run on the current machine."""

    @abstractmethod
    def speak(self, text: str, lang: str = "en") -> bool:
        """Synthesize and play *text*. Returns True on success."""
