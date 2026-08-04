"""Data models for the Conversation Manager.

These models are deliberately lightweight and avoid any external
dependencies so they can be used in any part of the code‑base without
pulling in heavy libraries.
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from typing import List, Any, Dict, Optional

# Phrases that turn prior assistant turns into bad personality few-shots.
_ASSISTANT_STYLE_RES = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"how can i (help|assist)( you)?( today)?\??",
        r"what can i (help|do) (you )?with\??",
        r"i'?d be happy to (help|assist)[^.!?]*[.!]?",
        r"i('m| am) (here to help|happy to help|here for you)[^.!?]*[.!]?",
        r"is there anything else i can (help|assist)[^.!?]*[.!]?",
        r"let me know if (you need|there'?s|i can)[^.!?]*[.!]?",
        r"as an ai[^.!?]*[.!]?",
        r"i (hear you|understand how you feel|understand your (feelings|frustration))[^.!?]*[.!]?",
        r"thank you for sharing[^.!?]*[.!]?",
        r"how does that make you feel\??",
        r"i remember you asking[^.!?]*[.!]?",
        r"\b(yaar|yar)\b[,!]?\s*",
        r"\bmadam(\s*ji)?\b[,!]?\s*",
        r"hey there[,!]?\s*(sanjay[,!]?\s*)?",
        r"sure[,!]?\s*(here'?s|i can)[^.!?]*[.!]?",
        r"of course[,!]?\s*(i('d| would) be happy)?[^.!?]*[.!]?",
    )
]

_HINGLISH_MARKERS = re.compile(
    r"\b(hai|hain|kya|nahi|nahin|mat|tum|tera|teri|mera|meri|haan|theek|"
    r"achha|accha|acha|bahut|kyun|kyu|kaise|kaisa|bolo|sun|suno|yaar|yar|bhai|"
    r"badi|baji|baje|abhi|karo|karna|chahiye|woh|yeh|iska|uska|rha|raha|rahi|"
    r"gaya|gayi|mujhe|tumhe|aap|ji|chalo|dekho|batao|sab|set|scene|vibe|"
    r"pakdo|final|sort|wala|wali|karti|karte|karu|bolte|na)\b",
    re.IGNORECASE,
)


def _compress_assistant_for_continuity(content: str) -> str:
    """Reduce prior reply to a short meaning note — never reusable dialogue."""
    text = (content or "").strip()
    if not text:
        return ""
    for pattern in _ASSISTANT_STYLE_RES:
        text = pattern.sub(" ", text)
    text = re.sub(r"[\"'`]", "", text)
    text = re.sub(r"\s+", " ", text).strip(" ,.!?;:-")
    if not text or len(text) < 12:
        return ""
    # Prefer a short factual gist over full prior wording.
    if len(text) > 80:
        cut = text[:80]
        if " " in cut:
            cut = cut.rsplit(" ", 1)[0]
        text = cut.strip(" ,.!?;:-")
    return text


_OFF_TOPIC_GIST_MARKERS = (
    "cocktail recipe",
    "margarita",
    "mojito",
    "goa weather",
    "your name is sanjay",
    "cockpit is ready",
    "cockpit ready",
)


def _is_low_value_gist(gist: str) -> bool:
    """Drop long or off-topic assistant gists from continuity."""
    lower = (gist or "").lower()
    if not lower:
        return True
    if len(gist) > 90:
        return True
    return any(marker in lower for marker in _OFF_TOPIC_GIST_MARKERS)


def format_messages_for_prompt(messages: List[Dict[str, str]]) -> str:
    """Build semantic session state — not reusable dialogue few-shots.

    Preserves: user intent, recent user points, facts/decisions.
    Drops: assistant wording, tone, style, full generated sentences.
    """
    if not messages:
        return ""

    user_points: List[str] = []
    decisions: List[str] = []
    for msg in messages:
        role = (msg.get("role") or "unknown").lower()
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        if role in ("user", "human"):
            user_points.append(content[:220])
        elif role in ("assistant", "bot", "zesty"):
            gist = _compress_assistant_for_continuity(content)
            if gist and not _is_low_value_gist(gist):
                decisions.append(gist)

    lines: List[str] = []
    if user_points:
        lines.append(f"Active user intent: {user_points[-1]}")
        prior_users = user_points[-3:-1]
        if prior_users:
            lines.append("Recent user points:")
            for point in prior_users:
                lines.append(f"- {point[:120]}")
    if decisions:
        lines.append("Established facts/decisions (meaning only — never copy wording or tone):")
        for item in decisions[-2:]:
            lines.append(f"- {item}")

    # Immediate prior turn (current user message is often already the latest in the list)
    if len(user_points) >= 2:
        lines.append(f"Previous user message: {user_points[-2]}")
    if decisions:
        lines.append(f"Your last reply (gist): {decisions[-1]}")

    return "\n".join(lines)


@dataclass(slots=True)
class SessionState:
    """Represents the high‑level state of a conversation session.

    Attributes
    ----------
    session_id: str
        Unique identifier for the session.
    created_at: datetime
        Timestamp when the session was created.
    last_interaction: datetime
        Timestamp of the most recent interaction.
    active_topic: Optional[str]
        Currently active topic, if any.
    previous_topic: Optional[str]
        Topic that was active before the current one.
    metadata: Dict[str, Any]
        Arbitrary key‑value pairs for extensions such as user id, locale, etc.
    """

    session_id: str
    created_at: _dt.datetime = field(default_factory=_dt.datetime.utcnow)
    last_interaction: _dt.datetime = field(default_factory=_dt.datetime.utcnow)
    active_topic: Optional[str] = None
    previous_topic: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        """Update ``last_interaction`` to now.
        """

        self.last_interaction = _dt.datetime.utcnow()

    def set_topic(self, new_topic: Optional[str]) -> None:
        """Switch the active topic, remembering the previous one.
        """

        self.previous_topic = self.active_topic
        self.active_topic = new_topic
        self.touch()


@dataclass(slots=True)
class WorkingMemory:
    """In‑memory store for conversation history.  Keeps the last N exchanges
    (or ``max_items`` items if you prefer a size cap) and can be queried
    for recent items or cleared at any time.
    """

    items: List[Any] = field(default_factory=list)
    max_items: int = 20                     # Keep the last 20 exchanges by default

    def add(self, item: Any) -> None:
        """Append *item* to the history and enforce the max-items limit."""
        self.items.append(item)
        if len(self.items) > self.max_items:
            # Drop oldest entries – keep the most recent ``max_items`` entries
            self.items = self.items[-self.max_items :]

    def recent(self, limit: int = 5) -> List[Any]:
        """Return the *limit* most recent items, newest first."""
        return list(reversed(self.items[-limit:]))

    def clear(self) -> None:
        """Remove all stored items."""
        self.items.clear()


@dataclass(slots=True)
class StructuredWorkingMemory:
    """Session-scoped working memory for tracking structured conversational
    state such as the active project, current task, goals, pending actions
    and the current topic.

    This is **not** persisted to long-term storage – it lives only for the
    duration of a single conversation session.
    """

    active_project: Optional[str] = None
    current_task: Optional[str] = None
    goals: List[str] = field(default_factory=list)
    pending_actions: List[str] = field(default_factory=list)
    topic: Optional[str] = None

    def update_project(self, project: Optional[str]) -> None:
        """Set the active project."""
        self.active_project = project

    def update_task(self, task: Optional[str]) -> None:
        """Set the current task."""
        self.current_task = task

    def add_goal(self, goal: str) -> None:
        """Append a goal to the working memory."""
        if goal and goal not in self.goals:
            self.goals.append(goal)

    def remove_goal(self, goal: str) -> None:
        """Remove a goal from the working memory."""
        if goal in self.goals:
            self.goals.remove(goal)

    def add_pending_action(self, action: str) -> None:
        """Append a pending action."""
        if action and action not in self.pending_actions:
            self.pending_actions.append(action)

    def remove_pending_action(self, action: str) -> None:
        """Remove a pending action."""
        if action in self.pending_actions:
            self.pending_actions.remove(action)

    def update_topic(self, topic: Optional[str]) -> None:
        """Set the current topic."""
        self.topic = topic

    def to_context(self) -> str:
        """Return a concise string representation suitable for prompt injection."""
        parts: List[str] = []
        if self.active_project:
            parts.append(f"Project: {self.active_project}")
        if self.current_task:
            parts.append(f"Task: {self.current_task}")
        if self.goals:
            parts.append(f"Goals: {', '.join(self.goals)}")
        if self.pending_actions:
            parts.append(f"Pending: {', '.join(self.pending_actions)}")
        if self.topic:
            parts.append(f"Topic: {self.topic}")
        return "; ".join(parts) if parts else ""


@dataclass(slots=True)
class ConversationHistory:
    """Stores the last N messages of a conversation session.

    Messages are stored as dictionaries with ``role`` and ``content`` keys.
    When the limit is exceeded, older messages are automatically trimmed.
    """

    messages: List[Dict[str, str]] = field(default_factory=list)
    max_messages: int = 20

    def add(self, role: str, content: str) -> None:
        """Add a message to the history, trimming older entries if needed."""
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def get_formatted(self) -> str:
        """Return prompt-safe conversation continuity (sanitized assistant turns)."""
        return format_messages_for_prompt(self.messages)

    def clear(self) -> None:
        """Remove all messages."""
        self.messages.clear()

    def __len__(self) -> int:
        return len(self.messages)

    def to_serializable(self) -> List[Dict[str, Any]]:
        """Return a copy suitable for JSON/YAML serialization."""
        # Keep only content and role for serialization; discard ephemeral objects
        return [{"role": {"human": "user", "assistant": "bot"}[repr(item).split(".")[0]], "content": item} 
                for item in self.messages]
