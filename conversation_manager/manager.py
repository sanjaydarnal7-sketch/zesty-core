"""Thread-safe Conversation Manager service.

The design keeps all mutable state inside per-session objects that are
protected by a single ``threading.RLock``.  This guarantees correctness
even when the service is accessed from multiple threads (e.g. a FastAPI
endpoint pool).

Only standard library modules are used so the manager can be imported
anywhere without pulling heavy optional dependencies.
"""

from __future__ import annotations

import threading
from typing import Dict, Any, List, Optional, Union

from .models import (
    SessionState,
    WorkingMemory,
    StructuredWorkingMemory,
    ConversationHistory,
    format_messages_for_prompt,
)
from .tracker import TopicTracker


class ConversationManager:
    """Standalone service that maintains conversation context.

    The manager does **not** touch Flask routing or any other framework –
    it is a pure Python object that can be instantiated and injected where
    needed.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sessions: Dict[str, SessionState] = {}
        self._memory: Dict[str, WorkingMemory] = {}
        self._structured_memory: Dict[str, StructuredWorkingMemory] = {}
        self._history: Dict[str, ConversationHistory] = {}
        self._topics: Dict[str, TopicTracker] = {}

    # ---------------------------------------------------------------------
    # Session lifecycle
    # ---------------------------------------------------------------------
    def start_session(self, session_id: str, *, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Create a new conversation session.

        Raises
        ------
        ValueError
            If a session with the same *session_id* already exists.
        """
        with self._lock:
            if session_id in self._sessions:
                raise ValueError(f"Session '{session_id}' already exists")
            self._sessions[session_id] = SessionState(session_id=session_id, metadata=metadata or {})
            self._memory[session_id] = WorkingMemory()
            self._structured_memory[session_id] = StructuredWorkingMemory()
            self._history[session_id] = ConversationHistory()
            self._topics[session_id] = TopicTracker()

    def end_session(self, session_id: str) -> None:
        """Remove all data for *session_id*.
        """
        with self._lock:
            self._sessions.pop(session_id, None)
            self._memory.pop(session_id, None)
            self._structured_memory.pop(session_id, None)
            self._history.pop(session_id, None)
            self._topics.pop(session_id, None)

    def has_session(self, session_id: str) -> bool:
        """Return ``True`` if *session_id* exists."""
        with self._lock:
            return session_id in self._sessions

    def ensure_session(self, session_id: str, *, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Create *session_id* if it does not already exist."""
        with self._lock:
            if session_id not in self._sessions:
                self.start_session(session_id, metadata=metadata)

    # ---------------------------------------------------------------------
    # Conversation history
    # ---------------------------------------------------------------------
    def add_message(self, session_id: str, role: Union[str, Dict[str, Any]], content: Optional[str] = None) -> None:
        """Add a message to the conversation history and update timestamps.

        Supports both calling styles for backward compatibility:
        - add_message(session_id, "user", "Hello")
        - add_message(session_id, {"role": "user", "content": "Hello"})
        """
        # Handle backward compatibility: if role is a dict, extract role/content
        if isinstance(role, dict):
            message = role
            role = message.get("role", "user")
            content = message.get("content", "")
        elif content is None:
            content = ""
        
        with self._lock:
            self._ensure_session(session_id)
            self._history[session_id].add(role, content)
            # Also add to working memory for backward compatibility
            self._memory[session_id].add({"role": role, "content": content})
            self._sessions[session_id].touch()

    def get_conversation_history(self, session_id: str, *, limit: Optional[int] = None) -> str:
        """Return prompt-safe conversation continuity, optionally limited to last N messages."""
        with self._lock:
            self._ensure_session(session_id)
            history = self._history[session_id]
            if limit is None:
                return history.get_formatted()
            messages = history.messages[-limit:] if len(history.messages) > limit else history.messages
            return format_messages_for_prompt(messages)

    def clear_conversation_history(self, session_id: str) -> None:
        """Remove all messages from the conversation history."""
        with self._lock:
            self._ensure_session(session_id)
            self._history[session_id].clear()

    # ---------------------------------------------------------------------
    # Structured working memory
    # ---------------------------------------------------------------------
    def get_structured_memory(self, session_id: str) -> StructuredWorkingMemory:
        """Return the structured working memory for a session."""
        with self._lock:
            self._ensure_session(session_id)
            return self._structured_memory[session_id]

    def update_project(self, session_id: str, project: Optional[str]) -> None:
        """Set the active project in structured working memory."""
        with self._lock:
            self._ensure_session(session_id)
            self._structured_memory[session_id].update_project(project)

    def update_task(self, session_id: str, task: Optional[str]) -> None:
        """Set the current task in structured working memory."""
        with self._lock:
            self._ensure_session(session_id)
            self._structured_memory[session_id].update_task(task)

    def add_goal(self, session_id: str, goal: str) -> None:
        """Add a goal to structured working memory."""
        with self._lock:
            self._ensure_session(session_id)
            self._structured_memory[session_id].add_goal(goal)

    def remove_goal(self, session_id: str, goal: str) -> None:
        """Remove a goal from structured working memory."""
        with self._lock:
            self._ensure_session(session_id)
            self._structured_memory[session_id].remove_goal(goal)

    def add_pending_action(self, session_id: str, action: str) -> None:
        """Add a pending action to structured working memory."""
        with self._lock:
            self._ensure_session(session_id)
            self._structured_memory[session_id].add_pending_action(action)

    def remove_pending_action(self, session_id: str, action: str) -> None:
        """Remove a pending action from structured working memory."""
        with self._lock:
            self._ensure_session(session_id)
            self._structured_memory[session_id].remove_pending_action(action)

    def update_topic_structured(self, session_id: str, topic: Optional[str]) -> None:
        """Set the current topic in structured working memory."""
        with self._lock:
            self._ensure_session(session_id)
            self._structured_memory[session_id].update_topic(topic)

    def get_structured_context(self, session_id: str) -> str:
        """Return a concise string representation of structured working memory."""
        with self._lock:
            self._ensure_session(session_id)
            return self._structured_memory[session_id].to_context()

    # ---------------------------------------------------------------------
    # Legacy helpers (maintain backward compatibility)
    # ---------------------------------------------------------------------
    def add(self, session_id: str, message: Any) -> None:
        """Append *message* to the working memory of *session_id* and bump timestamps."""
        with self._lock:
            self._ensure_session(session_id)
            self._memory[session_id].add(message)
            self._sessions[session_id].touch()

    def get_context(self, session_id: str, *, recent_limit: int = 10) -> Dict[str, Any]:
        """Retrieve a snapshot of the conversation context.

        The returned dictionary contains:

        * ``session_state`` – the :class:`SessionState` instance.
        * ``recent_memory`` – list of recent messages.
        * ``active_topic`` and ``previous_topic`` – current topic information.
        """
        with self._lock:
            self._ensure_session(session_id)
            state = self._sessions[session_id]
            memory = self._memory[session_id].recent(limit=recent_limit)
            tracker = self._topics[session_id]
            return {
                "session_state": state,
                "recent_memory": memory,
                "active_topic": tracker.get_current(),
                "previous_topic": tracker.get_previous(),
            }

    # ---------------------------------------------------------------------
    # Interaction helpers
    # ---------------------------------------------------------------------
    def set_active_topic(self, session_id: str, topic: Optional[str]) -> None:
        """Update the active topic for *session_id* (legacy method)."""
        with self._lock:
            self._ensure_session(session_id)
            self._topics[session_id].set_topic(topic)
            self._sessions[session_id].set_topic(topic)

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _ensure_session(self, session_id: str) -> None:
        if session_id not in self._sessions:
            raise KeyError(f"Session '{session_id}' does not exist")
