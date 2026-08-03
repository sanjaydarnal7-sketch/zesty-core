"""
Conversation Manager package.

Provides thread-safe conversation state management including:
- Conversation history (last N messages per session)
- Structured working memory (project, task, goals, pending actions, topic)
- Session state tracking
- Topic tracking

Public API:
    ConversationManager  – Main service class
    SessionState         – Session metadata
    WorkingMemory        – Unstructured message history
    StructuredWorkingMemory – Structured session context
    ConversationHistory  – Formatted message history
    TopicTracker         – Active/previous topic tracking
"""
from .models import (
    SessionState,
    WorkingMemory,
    StructuredWorkingMemory,
    ConversationHistory,
)
from .tracker import TopicTracker
from .manager import ConversationManager

__all__ = [
    "ConversationManager",
    "SessionState",
    "WorkingMemory",
    "StructuredWorkingMemory",
    "ConversationHistory",
    "TopicTracker",
]

__version__ = "1.1.0"
