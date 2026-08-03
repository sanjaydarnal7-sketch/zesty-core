"""Thread-safe Working Memory Engine for Zesty OS.

The engine maintains session-scoped working memory that tracks the
cognitive state of a conversation: current topic, active project, goals,
pending tasks, open questions, user intent, recent decisions, active
file, and current mode.

Design principles:
- **Thread-safe**: All public methods acquire a re-entrant lock.
- **Session-scoped only**: State lives only for the lifetime of a session.
- **Pure Python**: No external dependencies.
- **Configurable expiration**: Each session can have its own TTL.
- **Clear/reset support**: Sessions can be reset or fully removed.
- **Export for Prompt Builder**: State can be exported as a formatted string.

Integration points for Prompt Assembly (next sprint):
- ``export_for_prompt(session_id)`` returns a ready-to-inject string.
- ``get_state(session_id)`` returns the raw :class:`WorkingMemoryState`.
- ``is_expired(session_id)`` lets the Prompt Builder skip stale sessions.
"""

from __future__ import annotations

import threading
from typing import Dict, Optional, List, Any

from .state import WorkingMemoryState


class WorkingMemoryEngine:
    """Manages working memory state for multiple conversation sessions.

    The engine is thread-safe and can be shared across threads (e.g. a
    FastAPI endpoint pool).  Each session's state is isolated from others.

    Parameters
    ----------
    default_ttl_seconds: Optional[int]
        Default time-to-live in seconds for new sessions.  If ``None``,
        sessions never expire by default.
    """

    def __init__(self, default_ttl_seconds: Optional[int] = None) -> None:
        self._lock = threading.RLock()
        self._sessions: Dict[str, WorkingMemoryState] = {}
        self._default_ttl_seconds: Optional[int] = default_ttl_seconds

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------
    def create_session(
        self,
        session_id: str,
        *,
        ttl_seconds: Optional[int] = None,
        initial_state: Optional[Dict[str, Any]] = None,
    ) -> WorkingMemoryState:
        """Create a new working memory session.

        Parameters
        ----------
        session_id: str
            Unique identifier for the session.
        ttl_seconds: Optional[int]
            Time-to-live for this session.  If ``None``, uses the engine's
            default.  If both are ``None``, the session never expires.
        initial_state: Optional[Dict[str, Any]]
            Optional initial values for the state fields.

        Returns
        -------
        WorkingMemoryState
            The newly created state object.

        Raises
        ------
        ValueError
            If a session with the same *session_id* already exists.
        """
        with self._lock:
            if session_id in self._sessions:
                raise ValueError(f"Session '{session_id}' already exists")

            if initial_state:
                state = WorkingMemoryState.from_dict(initial_state)
            else:
                state = WorkingMemoryState()

            ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl_seconds
            if ttl is not None:
                state.set_expiration(ttl)

            self._sessions[session_id] = state
            return state

    def ensure_session(self, session_id: str) -> WorkingMemoryState:
        """Return session state, creating it when missing."""
        with self._lock:
            if session_id not in self._sessions:
                return self.create_session(session_id)
            return self._sessions[session_id]

    def set_metadata(self, session_id: str, key: str, value: Any) -> None:
        """Set a metadata key on the session working memory state."""
        with self._lock:
            state = self.ensure_session(session_id)
            state.metadata[key] = value
            state.touch()

    def get_metadata(self, session_id: str, key: str, default: Any = None) -> Any:
        """Read a metadata key from the session working memory state."""
        with self._lock:
            if session_id not in self._sessions:
                return default
            return self._sessions[session_id].metadata.get(key, default)

    def get_session(self, session_id: str) -> WorkingMemoryState:
        """Retrieve the state for *session_id*.

        Raises
        ------
        KeyError
            If the session does not exist.
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' does not exist")
            return self._sessions[session_id]

    def has_session(self, session_id: str) -> bool:
        """Return ``True`` if *session_id* exists."""
        with self._lock:
            return session_id in self._sessions

    def delete_session(self, session_id: str) -> bool:
        """Remove a session entirely.

        Returns
        -------
        bool
            ``True`` if the session was removed, ``False`` if it did not exist.
        """
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def reset_session(self, session_id: str) -> WorkingMemoryState:
        """Reset a session's state to defaults while keeping the session.

        This clears all tracked fields but preserves the session's
        expiration settings.

        Raises
        ------
        KeyError
            If the session does not exist.
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' does not exist")

            old_state = self._sessions[session_id]
            new_state = WorkingMemoryState()

            # Preserve expiration if it was set
            if old_state.expires_at is not None:
                new_state.expires_at = old_state.expires_at

            self._sessions[session_id] = new_state
            return new_state

    def clear_all_sessions(self) -> int:
        """Remove all sessions.

        Returns
        -------
        int
            The number of sessions that were removed.
        """
        with self._lock:
            count = len(self._sessions)
            self._sessions.clear()
            return count

    def list_sessions(self) -> List[str]:
        """Return a list of all active session IDs."""
        with self._lock:
            return list(self._sessions.keys())

    def cleanup_expired(self) -> int:
        """Remove all expired sessions.

        Returns
        -------
        int
            The number of sessions that were removed.
        """
        with self._lock:
            expired_ids = [
                sid for sid, state in self._sessions.items()
                if state.is_expired()
            ]
            for sid in expired_ids:
                del self._sessions[sid]
            return len(expired_ids)

    # ------------------------------------------------------------------
    # State accessors
    # ------------------------------------------------------------------
    def get_state(self, session_id: str) -> WorkingMemoryState:
        """Alias for :meth:`get_session`."""
        return self.get_session(session_id)

    def is_expired(self, session_id: str) -> bool:
        """Check whether a session's state has expired.

        Raises
        ------
        KeyError
            If the session does not exist.
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' does not exist")
            return self._sessions[session_id].is_expired()

    def set_expiration(self, session_id: str, ttl_seconds: int) -> None:
        """Set or update the expiration time for a session.

        Raises
        ------
        KeyError
            If the session does not exist.
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' does not exist")
            self._sessions[session_id].set_expiration(ttl_seconds)

    def clear_expiration(self, session_id: str) -> None:
        """Remove the expiration for a session, making it persistent.

        Raises
        ------
        KeyError
            If the session does not exist.
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' does not exist")
            self._sessions[session_id].clear_expiration()

    # ------------------------------------------------------------------
    # State mutators
    # ------------------------------------------------------------------
    def _update_field(self, session_id: str, field_name: str, value: Any) -> None:
        """Internal helper to update a single field and touch the state."""
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' does not exist")
            setattr(self._sessions[session_id], field_name, value)
            self._sessions[session_id].touch()

    def set_current_topic(self, session_id: str, topic: Optional[str]) -> None:
        """Set the current topic for a session."""
        self._update_field(session_id, "current_topic", topic)

    def set_active_project(self, session_id: str, project: Optional[str]) -> None:
        """Set the active project for a session."""
        self._update_field(session_id, "active_project", project)

    def set_current_goal(self, session_id: str, goal: Optional[str]) -> None:
        """Set the current goal for a session."""
        self._update_field(session_id, "current_goal", goal)

    def set_user_intent(self, session_id: str, intent: Optional[str]) -> None:
        """Set the user intent for a session."""
        self._update_field(session_id, "user_intent", intent)

    def set_active_file(self, session_id: str, file_path: Optional[str]) -> None:
        """Set the active file for a session."""
        self._update_field(session_id, "active_file", file_path)

    def set_current_mode(self, session_id: str, mode: Optional[str]) -> None:
        """Set the current mode for a session."""
        self._update_field(session_id, "current_mode", mode)

    # ------------------------------------------------------------------
    # List-based field operations
    # ------------------------------------------------------------------
    def add_pending_task(self, session_id: str, task: str) -> None:
        """Add a pending task to a session."""
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' does not exist")
            state = self._sessions[session_id]
            if task and task not in state.pending_tasks:
                state.pending_tasks.append(task)
                state.touch()

    def remove_pending_task(self, session_id: str, task: str) -> bool:
        """Remove a pending task from a session.

        Returns
        -------
        bool
            ``True`` if the task was found and removed, ``False`` otherwise.
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' does not exist")
            state = self._sessions[session_id]
            if task in state.pending_tasks:
                state.pending_tasks.remove(task)
                state.touch()
                return True
            return False

    def add_open_question(self, session_id: str, question: str) -> None:
        """Add an open question to a session."""
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' does not exist")
            state = self._sessions[session_id]
            if question and question not in state.open_questions:
                state.open_questions.append(question)
                state.touch()

    def remove_open_question(self, session_id: str, question: str) -> bool:
        """Remove an open question from a session.

        Returns
        -------
        bool
            ``True`` if the question was found and removed, ``False`` otherwise.
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' does not exist")
            state = self._sessions[session_id]
            if question in state.open_questions:
                state.open_questions.remove(question)
                state.touch()
                return True
            return False

    def add_recent_decision(self, session_id: str, decision: str) -> None:
        """Add a recent decision to a session."""
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' does not exist")
            state = self._sessions[session_id]
            if decision:
                state.recent_decisions.append(decision)
                state.touch()

    def get_recent_decisions(self, session_id: str, limit: Optional[int] = None) -> List[str]:
        """Get recent decisions for a session, optionally limited to *limit* items.

        Raises
        ------
        KeyError
            If the session does not exist.
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' does not exist")
            decisions = self._sessions[session_id].recent_decisions
            if limit is not None:
                return decisions[-limit:]
            return list(decisions)

    # ------------------------------------------------------------------
    # Export for Prompt Builder
    # ------------------------------------------------------------------
    def export_for_prompt(self, session_id: str) -> str:
        """Export the working memory state as a formatted string for prompt injection.

        Returns an empty string if the session has no tracked state.

        Raises
        ------
        KeyError
            If the session does not exist.
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' does not exist")
            return self._sessions[session_id].export_for_prompt()

    def export_as_dict(self, session_id: str) -> Dict[str, Any]:
        """Export the working memory state as a dictionary.

        Raises
        ------
        KeyError
            If the session does not exist.
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' does not exist")
            return self._sessions[session_id].to_dict()
