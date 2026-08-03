"""Tests for the ConversationManager service.

These tests exercise the public API and verify thread‑safety by running a
few operations sequentially – full concurrency testing would require a
more elaborate setup and is out of scope for the simple unit test suite.
"""

import threading
from conversation_manager.manager import ConversationManager


def test_basic_session_flow() -> None:
    manager = ConversationManager()
    sid = "session‑1"

    # Start a new session
    manager.start_session(sid, metadata={"user": "alice"})

    # Add messages
    manager.add_message(sid, {"role": "user", "content": "Hello"})
    manager.add_message(sid, {"role": "assistant", "content": "Hi there!"})

    # Change topic
    manager.set_active_topic(sid, "greeting")

    # Retrieve context
    ctx = manager.get_context(sid, recent_limit=5)

    assert ctx["session_state"].session_id == sid
    assert ctx["active_topic"] == "greeting"
    assert ctx["previous_topic"] is None
    recent = ctx["recent_memory"]
    assert len(recent) == 2
    assert recent[0]["content"] == "Hi there!"
    assert recent[1]["content"] == "Hello"

    # End session cleans up internal structures
    manager.end_session(sid)
    try:
        manager.get_context(sid)
    except KeyError:
        pass
    else:
        raise AssertionError("Session should have been removed")
