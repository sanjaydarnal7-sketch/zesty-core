"""Conversation module for Zesty OS.

This package provides session-scoped conversation utilities including
working memory management, conversation history, and prompt formatting.

Modules:
- ``state``: WorkingMemoryState dataclass for tracking session state.
- ``working_memory``: Thread-safe WorkingMemoryEngine for managing sessions.
"""

from .state import WorkingMemoryState
from .working_memory import WorkingMemoryEngine

__all__ = ["WorkingMemoryState", "WorkingMemoryEngine"]
