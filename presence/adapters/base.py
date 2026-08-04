"""
Adapter interfaces for wake word, camera, and voice identity.

Electron / native services implement these; the Flask era uses stubs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from presence.models import DetectionResult, WakeSource


class WakeWordAdapter(ABC):
    """Listens for 'Hey Zesty' and signals wake events."""

    @abstractmethod
    def start(self) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...

    @abstractmethod
    def poll_wake(self) -> WakeSource | None:
        """Non-blocking check for a wake event since last poll."""
        ...


class FaceRecognitionAdapter(ABC):
    """Scans camera frames and returns identity matches."""

    @abstractmethod
    def scan_frame(self, frame: Any = None) -> DetectionResult | None:
        ...

    @abstractmethod
    def enroll_face(self, identity_id: str, frame: Any = None) -> bool:
        ...


class VoiceIdentityAdapter(ABC):
    """Speaker identification from audio — secondary-person awareness."""

    @abstractmethod
    def identify_speaker(self, audio: Any = None) -> DetectionResult | None:
        ...

    @abstractmethod
    def enroll_voice(self, identity_id: str, audio: Any = None) -> bool:
        ...
