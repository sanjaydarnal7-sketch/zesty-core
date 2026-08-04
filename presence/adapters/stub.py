"""No-op adapters for Flask/browser era — API and manual wake only."""

from __future__ import annotations

from typing import Any

from presence.adapters.base import FaceRecognitionAdapter, VoiceIdentityAdapter, WakeWordAdapter
from presence.models import DetectionResult, WakeSource


class StubWakeWordAdapter(WakeWordAdapter):
    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def poll_wake(self) -> WakeSource | None:
        return None


class StubFaceRecognitionAdapter(FaceRecognitionAdapter):
    def scan_frame(self, frame: Any = None) -> DetectionResult | None:
        return None

    def enroll_face(self, identity_id: str, frame: Any = None) -> bool:
        return False


class StubVoiceIdentityAdapter(VoiceIdentityAdapter):
    def identify_speaker(self, audio: Any = None) -> DetectionResult | None:
        return None

    def enroll_voice(self, identity_id: str, audio: Any = None) -> bool:
        return False
