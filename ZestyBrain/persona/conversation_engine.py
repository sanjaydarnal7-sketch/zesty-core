"""
Zesty Conversation Engine

Controls how Zesty speaks based on the detected emotional state.
"""

from __future__ import annotations

from ZestyBrain.persona.emotion_engine import EmotionState


class ConversationEngine:

    def build_style(self, emotion: EmotionState) -> str:

        if emotion.mood == "excited":
            return (
                "Match the user's excitement naturally. "
                "Be energetic, positive and motivating without overdoing it."
            )

        if emotion.mood == "frustrated":
            return (
                "Stay calm. Reduce the user's stress. "
                "Explain clearly. Focus on solving the problem."
            )

        if emotion.mood == "urgent":
            return (
                "Be direct. Prioritize speed and clarity. "
                "Avoid unnecessary explanations."
            )

        return (
            "Be natural, relaxed, conversational and helpful."
        )
