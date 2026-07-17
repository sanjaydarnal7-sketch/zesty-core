"""
Zesty OS
Reflex Engine

ADR-004

The Reflex Engine is responsible for immediate conversational
behaviours that should happen without waiting for LLM reasoning.

Examples:
- Backchannel responses ("Hmm", "I see", "Go on")
- Listening acknowledgements
- Future interruption handling

Version: 1.0
"""

from __future__ import annotations

from typing import Any


class ReflexEngine:
    """
    Handles ultra-fast conversational reflexes.

    NOTE:
    This is currently a production-ready stub.
    Behaviour will be implemented in future missions.
    """

    def __init__(self) -> None:
        self.enabled = True

    def handle_speech_started(self) -> None:
        """
        Called when speech begins.
        """
        if not self.enabled:
            return

    def handle_partial_speech(self, text: str) -> None:
        """
        Called while speech is still streaming.
        """
        if not self.enabled:
            return

    def handle_speech_finished(self) -> None:
        """
        Called after speech has finished.
        """
        if not self.enabled:
            return

    def request_backchannel(self) -> Any:
        """
        Future implementation will decide whether
        a backchannel response should be played.

        Returns:
            None for now.
        """
        return None