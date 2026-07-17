"""
Zesty OS
Conversation Orchestrator

ADR-004

Coordinates the conversation pipeline by connecting
the Runtime Event Bus with conversation components.

Current Version:
Production-ready orchestration stub.
"""

from __future__ import annotations

from core.runtime_event_bus import RuntimeEventBus
from conversation.reflex_engine import ReflexEngine

from events.conversation_events import (
    SPEECH_STARTED,
    SPEECH_PARTIAL,
    SPEECH_FINISHED,
)


class ConversationOrchestrator:
    """
    Coordinates conversation-related runtime events.

    This class intentionally contains very little logic.
    Heavy processing should be delegated to dedicated
    engines (ASR, Memory, Emotion, LLM, etc.).
    """

    def __init__(self, event_bus: RuntimeEventBus) -> None:
        self.event_bus = event_bus
        self.reflex = ReflexEngine()

        self._register_events()

    def _register_events(self) -> None:
        """Register conversation event listeners."""

        self.event_bus.subscribe(
            SPEECH_STARTED,
            self._on_speech_started,
        )

        self.event_bus.subscribe(
            SPEECH_PARTIAL,
            self._on_speech_partial,
        )

        self.event_bus.subscribe(
            SPEECH_FINISHED,
            self._on_speech_finished,
        )

    def _on_speech_started(self, event) -> None:
        self.reflex.handle_speech_started()

    def _on_speech_partial(self, event) -> None:
        text = getattr(event, "payload", "")
        self.reflex.handle_partial_speech(text)

    def _on_speech_finished(self, event) -> None:
        self.reflex.handle_speech_finished()