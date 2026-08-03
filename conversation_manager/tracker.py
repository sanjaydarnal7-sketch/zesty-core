"""Utility for tracking active and previous topics.

The tracker is deliberately tiny – it does not own any persistence or
locking; the :class:`ConversationManager` coordinates thread‑safety.
"""

from __future__ import annotations

from typing import Optional


class TopicTracker:
    """Tracks the current and previous conversation topics.

    The class is purposefully simple – it just holds two strings and offers
    a method to update them atomically.
    """

    __slots__ = ("active_topic", "previous_topic")

    def __init__(self, initial_topic: Optional[str] = None) -> None:
        self.active_topic: Optional[str] = initial_topic
        self.previous_topic: Optional[str] = None

    def set_topic(self, new_topic: Optional[str]) -> None:
        """Set *new_topic* as the active one, moving the current active to *previous*.
        """
        self.previous_topic = self.active_topic
        self.active_topic = new_topic

    def get_current(self) -> Optional[str]:
        return self.active_topic

    def get_previous(self) -> Optional[str]:
        return self.previous_topic
