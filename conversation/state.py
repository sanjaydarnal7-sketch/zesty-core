"""State models for the Working Memory Engine.

These models are deliberately lightweight and avoid any external
dependencies so they can be used in any part of the code-base without
pulling in heavy libraries.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class WorkingMemoryState:
    """Represents the complete working memory state for a single session.

    All fields are optional and default to ``None`` or empty collections,
    so a fresh state can be created without any arguments.

    Attributes
    ----------
    current_topic: Optional[str]
        The active topic of conversation.
    active_project: Optional[str]
        The project currently being worked on.
    current_goal: Optional[str]
        The primary objective the session is pursuing.
    pending_tasks: List[str]
        Ordered list of tasks that still need to be completed.
    open_questions: List[str]
        Questions that have been raised but not yet answered.
    user_intent: Optional[str]
        The inferred intent behind the user's current request.
    recent_decisions: List[str]
        Decisions made during the session, most recent last.
    active_file: Optional[str]
        The file currently being edited or referenced.
    current_mode: Optional[str]
        The operational mode (e.g. "planning", "coding", "review").
    metadata: Dict[str, Any]
        Arbitrary key-value pairs for extensions.
    created_at: datetime
        Timestamp when this state was first created.
    updated_at: datetime
        Timestamp of the most recent update to this state.
    expires_at: Optional[datetime]
        Timestamp after which this state should be considered expired.
    """

    current_topic: Optional[str] = None
    active_project: Optional[str] = None
    current_goal: Optional[str] = None
    pending_tasks: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    user_intent: Optional[str] = None
    recent_decisions: List[str] = field(default_factory=list)
    active_file: Optional[str] = None
    current_mode: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: _dt.datetime = field(default_factory=_dt.datetime.utcnow)
    updated_at: _dt.datetime = field(default_factory=_dt.datetime.utcnow)
    expires_at: Optional[_dt.datetime] = None

    def touch(self) -> None:
        """Update ``updated_at`` to the current time."""
        self.updated_at = _dt.datetime.utcnow()

    def is_expired(self, now: Optional[_dt.datetime] = None) -> bool:
        """Return ``True`` if the state has passed its expiration time.

        If ``expires_at`` is ``None``, the state never expires.
        """
        if self.expires_at is None:
            return False
        check_time = now if now is not None else _dt.datetime.utcnow()
        return check_time >= self.expires_at

    def set_expiration(self, ttl_seconds: int) -> None:
        """Set the expiration time to *ttl_seconds* from now.

        Parameters
        ----------
        ttl_seconds: int
            Number of seconds from now until the state expires.
            Must be non-negative.
        """
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must be non-negative")
        self.expires_at = _dt.datetime.utcnow() + _dt.timedelta(seconds=ttl_seconds)

    def clear_expiration(self) -> None:
        """Remove the expiration time, making the state persistent."""
        self.expires_at = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return {
            "current_topic": self.current_topic,
            "active_project": self.active_project,
            "current_goal": self.current_goal,
            "pending_tasks": list(self.pending_tasks),
            "open_questions": list(self.open_questions),
            "user_intent": self.user_intent,
            "recent_decisions": list(self.recent_decisions),
            "active_file": self.active_file,
            "current_mode": self.current_mode,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkingMemoryState":
        """Create a state instance from a dictionary (inverse of :meth:`to_dict`)."""
        return cls(
            current_topic=data.get("current_topic"),
            active_project=data.get("active_project"),
            current_goal=data.get("current_goal"),
            pending_tasks=list(data.get("pending_tasks", [])),
            open_questions=list(data.get("open_questions", [])),
            user_intent=data.get("user_intent"),
            recent_decisions=list(data.get("recent_decisions", [])),
            active_file=data.get("active_file"),
            current_mode=data.get("current_mode"),
            metadata=dict(data.get("metadata", {})),
            created_at=_dt.datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else _dt.datetime.utcnow(),
            updated_at=_dt.datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else _dt.datetime.utcnow(),
            expires_at=_dt.datetime.fromisoformat(data["expires_at"])
            if data.get("expires_at")
            else None,
        )

    def export_for_prompt(self) -> str:
        """Return a concise string representation suitable for prompt injection.

        Only non-empty fields are included, separated by newlines.
        """
        parts: List[str] = []
        if self.current_topic:
            parts.append(f"Topic: {self.current_topic}")
        if self.active_project:
            parts.append(f"Project: {self.active_project}")
        if self.current_goal:
            parts.append(f"Goal: {self.current_goal}")
        if self.pending_tasks:
            parts.append(f"Pending: {', '.join(self.pending_tasks)}")
        if self.open_questions:
            parts.append(f"Questions: {', '.join(self.open_questions)}")
        if self.user_intent:
            parts.append(f"Intent: {self.user_intent}")
        if self.recent_decisions:
            parts.append(f"Decisions: {', '.join(self.recent_decisions)}")
        if self.active_file:
            parts.append(f"File: {self.active_file}")
        if self.current_mode:
            parts.append(f"Mode: {self.current_mode}")
        probe = self.metadata.get("last_deep_probe")
        if isinstance(probe, dict) and probe.get("name"):
            platform = probe.get("platform") or "web"
            parts.append(f"Active profile focus: {probe.get('name')} ({platform})")
        last_action = self.metadata.get("last_action")
        if isinstance(last_action, dict) and last_action.get("type"):
            subject = last_action.get("subject") or ""
            label = last_action["type"].replace("_", " ")
            parts.append(f"Last action: {label}" + (f" — {subject}" if subject else ""))
        return "\n".join(parts) if parts else ""
