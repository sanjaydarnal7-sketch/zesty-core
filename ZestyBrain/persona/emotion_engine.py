"""
Zesty Emotion Engine

Detects the user's emotional state from the current message.
This is intentionally lightweight and deterministic. It will
be upgraded later with memory and LLM-assisted emotion analysis.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmotionState:
    mood: str
    tone: str
    confidence: float


class EmotionEngine:

    def analyze(self, text: str) -> EmotionState:
        message = text.lower().strip()

        if any(word in message for word in [
            "wow", "awesome", "amazing", "great", "lets go",
            "let's go", "excited", "🔥", "🎉"
        ]):
            return EmotionState(
                mood="excited",
                tone="energetic",
                confidence=0.95,
            )

        if any(word in message for word in [
            "error", "issue", "problem", "stuck",
            "frustrated", "angry", "hate"
        ]):
            return EmotionState(
                mood="frustrated",
                tone="calm",
                confidence=0.90,
            )

        if any(word in message for word in [
            "urgent", "asap", "quick", "fast", "immediately"
        ]):
            return EmotionState(
                mood="urgent",
                tone="focused",
                confidence=0.90,
            )

        return EmotionState(
            mood="neutral",
            tone="natural",
            confidence=0.75,
        )
