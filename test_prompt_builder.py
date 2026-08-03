"""
Unit tests for the PromptBuilder and updated ConversationManager.

Run with:
    python -m pytest test_prompt_builder.py -v
"""
from __future__ import annotations

import pytest
from datetime import datetime

from conversation_manager.models import (
    SessionState,
    WorkingMemory,
    StructuredWorkingMemory,
    ConversationHistory,
)
from conversation_manager.manager import ConversationManager
from prompt_builder import PromptBuilder


# ---------------------------------------------------------------------------
# Mock objects for testing
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_persona():
    """Return a minimal persona JSON for test purposes."""
    return {
        "personaName": "Zesty",
        "slug": "zesty",
        "role": "assistant",
        "bio": "Test assistant persona.",
        "meta": {"framework": "openpersona", "frameworkVersion": "1.0.0"},
    }


@pytest.fixture
def sample_system_prompt():
    """Return a sample system prompt."""
    return "You are a helpful AI assistant."


@pytest.fixture
def populated_session(monkeypatch):
    """Create a populated conversation session for testing."""
    # Create manager and initialize session
    manager = ConversationManager()
    session_id = "test_session_123"
    manager.start_session(session_id, metadata={"user_id": "test_user"})

    # Add some conversation history
    manager.add_message(session_id, "user", "Hello, how are you?")
    manager.add_message(session_id, "assistant", "I'm doing well, thank you!")
    manager.add_message(session_id, "user", "What's the weather like today?")
    manager.add_message(session_id, "assistant", "It's sunny and 75°F outside.")

    # Update structured working memory
    struct_mem = manager.get_structured_memory(session_id)
    struct_mem.update_project("Weather Dashboard")
    struct_mem.update_task("Implement forecast feature")
    struct_mem.add_goal("Display 7-day forecast")
    struct_mem.add_pending_action("Fetch API data")
    struct_mem.update_topic("weather")

    # Add to unstructured memory
    manager.add(session_id, {"role": "system", "content": "System ready"})
    manager.add(session_id, {"role": "user", "content": "Check the calendar"})

    return manager, session_id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestStructuredWorkingMemory:
    """Tests for the StructuredWorkingMemory model."""

    def test_initialization(self):
        """Test that StructuredWorkingMemory initializes with empty values."""
        mem = StructuredWorkingMemory()
        assert mem.active_project is None
        assert mem.current_task is None
        assert mem.goals == []
        assert mem.pending_actions == []
        assert mem.topic is None

    def test_to_context_empty(self):
        """Test to_context() when all fields are empty."""
        mem = StructuredWorkingMemory()
        assert mem.to_context() == ""

    def test_to_context_partial(self):
        """Test to_context() with some fields populated."""
        mem = StructuredWorkingMemory(active_project="Test Project", topic="testing")
        result = mem.to_context()
        assert "Project: Test Project" in result
        assert "Topic: testing" in result
        assert "Task:" not in result

    def test_update_and_retrieve(self):
        """Test updating various fields."""
        mem = StructuredWorkingMemory()
        mem.update_project("Website Redesign")
        assert mem.active_project == "Website Redesign"

        mem.update_task("Create wireframes")
        assert mem.current_task == "Create wireframes"

        mem.add_goal("Improve user engagement")
        assert len(mem.goals) == 1
        assert "Improve user engagement" in mem.goals

        mem.add_pending_action("Schedule stakeholder meeting")
        assert len(mem.pending_actions) == 1
        assert "Schedule stakeholder meeting" in mem.pending_actions

        mem.update_topic("design")
        assert mem.topic == "design"


class TestConversationHistory:
    """Tests for the ConversationHistory model."""

    def test_initialization(self):
        """Test default initialization."""
        hist = ConversationHistory()
        assert len(hist) == 0
        assert hist.max_messages == 20

    def test_add_and_retrieve(self):
        """Test adding messages and retrieving formatted history."""
        hist = ConversationHistory()
        hist.add("user", "Hello")
        hist.add("assistant", "Hi there!")
        hist.add("user", "How are you?")

        assert len(hist) == 3

        formatted = hist.get_formatted()
        assert "[USER] Hello" in formatted
        assert "[ASSISTANT] Hi there!" in formatted
        assert "[USER] How are you?" in formatted

    def test_trimming(self):
        """Test that history trims old messages when exceeding max_messages."""
        hist = ConversationHistory(max_messages=3)
        for i in range(5):
            hist.add("user", f"Message {i}")

        # Should only keep the last 3
        assert len(hist) == 3
        formatted = hist.get_formatted()
        assert "Message 2" in formatted
        assert "Message 3" in formatted
        assert "Message 4" in formatted
        assert "Message 0" not in formatted  # Oldest should be dropped
        assert "Message 1" not in formatted

    def test_clear(self):
        """Test clearing history."""
        hist = ConversationHistory()
        hist.add("user", "Test")
        assert len(hist) == 1

        hist.clear()
        assert len(hist) == 0
        assert hist.get_formatted() == ""


class TestConversationManagerExtended:
    """Tests for the extended ConversationManager."""

    def test_session_lifecycle_with_new_structures(self):
        """Test that new structures are created when starting a session."""
        manager = ConversationManager()
        session_id = "test_new_struct"

        manager.start_session(session_id)

        # All structures should exist
        assert session_id in manager._sessions
        assert session_id in manager._memory
        assert session_id in manager._structured_memory
        assert session_id in manager._history
        assert session_id in manager._topics

        # Test types
        assert isinstance(manager._memory[session_id], WorkingMemory)
        assert isinstance(manager._structured_memory[session_id], StructuredWorkingMemory)
        assert isinstance(manager._history[session_id], ConversationHistory)
        assert isinstance(manager._topics[session_id], type(manager._topics[session_id]))

    def test_get_structured_memory(self, populated_session):
        """Test retrieving structured memory."""
        manager, session_id = populated_session
        struct_mem = manager.get_structured_memory(session_id)

        assert isinstance(struct_mem, StructuredWorkingMemory)
        assert struct_mem.active_project == "Weather Dashboard"
        assert struct_mem.current_task == "Implement forecast feature"
        assert "Display 7-day forecast" in struct_mem.goals
        assert "Fetch API data" in struct_mem.pending_actions
        assert struct_mem.topic == "weather"

    def test_structured_memory_updates(self):
        """Test updating structured memory fields."""
        manager = ConversationManager()
        session_id = "test_struct_update"
        manager.start_session(session_id)

        manager.update_project(session_id, "New Project")
        assert manager.get_structured_memory(session_id).active_project == "New Project"

        manager.add_goal(session_id, "New Goal")
        assert "New Goal" in manager.get_structured_memory(session_id).goals

        manager.remove_goal(session_id, "New Goal")
        assert "New Goal" not in manager.get_structured_memory(session_id).goals

        manager.add_pending_action(session_id, "New Action")
        assert "New Action" in manager.get_structured_memory(session_id).pending_actions

        manager.remove_pending_action(session_id, "New Action")
        assert "New Action" not in manager.get_structured_memory(session_id).pending_actions

        manager.update_topic_structured(session_id, "new topic")
        assert manager.get_structured_memory(session_id).topic == "new topic"

    def test_get_structured_context(self, populated_session):
        """Test getting formatted structured context."""
        manager, session_id = populated_session
        context = manager.get_structured_context(session_id)

        # Check that all expected fields appear
        assert "Project: Weather Dashboard" in context
        assert "Task: Implement forecast feature" in context
        assert "Goals: Display 7-day forecast" in context
        assert "Pending: Fetch API data" in context
        assert "Topic: weather" in context

    def test_add_and_get_conversation_history(self, populated_session):
        """Test adding messages and retrieving formatted history."""
        manager, session_id = populated_session

        # Add a new message
        manager.add_message(session_id, "user", "What time is it?")
        manager.add_message(session_id, "assistant", "It's 3:30 PM.")

        # Get formatted history
        history_str = manager.get_conversation_history(session_id)

        # Check all messages are present
        assert "[USER] Hello, how are you?" in history_str
        assert "[ASSISTANT] I'm doing well, thank you!" in history_str
        assert "[USER] What's the weather like today?" in history_str
        assert "[ASSISTANT] It's sunny and 75°F outside." in history_str
        assert "[USER] What time is it?" in history_str
        assert "[ASSISTANT] It's 3:30 PM." in history_str

    def test_conversation_history_limit(self):
        """Test that conversation history trims old messages."""
        manager = ConversationManager()
        session_id = "test_history_limit"
        manager.start_session(session_id)

        # Add more than 20 messages
        for i in range(25):
            manager.add_message(session_id, "user", f"Message {i}")
            manager.add_message(session_id, "assistant", f"Response {i}")

        # Should only keep last 20 pairs (40 messages)
        history_str = manager.get_conversation_history(session_id)
        # Check that oldest messages are not present
        assert "Message 0" not in history_str
        assert "Response 0" not in history_str
        # Check that recent messages are present
        assert "Message 24" in history_str
        assert "Response 24" in history_str

        # Verify exact count: 20 pairs = 40 messages
        lines = [line for line in history_str.split("\n") if line.strip()]
        assert len(lines) == 40

    def test_clear_conversation_history(self, populated_session):
        """Test clearing conversation history."""
        manager, session_id = populated_session
        manager.add_message(session_id, "user", "Last message")

        # Verify it exists
        assert manager.get_conversation_history(session_id) != ""

        # Clear it
        manager.clear_conversation_history(session_id)

        # Verify it's empty
        assert manager.get_conversation_history(session_id) == ""

    def test_structured_context_empty_session(self):
        """Test structured context for a fresh session."""
        manager = ConversationManager()
        session_id = "fresh_session"
        manager.start_session(session_id)

        context = manager.get_structured_context(session_id)
        assert context == ""  # Should be empty for new session


class TestPromptBuilder:
    """Tests for the PromptBuilder."""

    def test_initialization(self, sample_system_prompt, mock_persona):
        """Test that PromptBuilder initializes correctly."""
        builder = PromptBuilder(sample_system_prompt, mock_persona)
        assert builder.system_prompt == sample_system_prompt
        assert builder.persona_json == mock_persona

    def test_build_basic(self, sample_system_prompt, mock_persona):
        """Test basic prompt building."""
        builder = PromptBuilder(sample_system_prompt, mock_persona)
        result = builder.build("dummy_session")

        # Should contain system prompt
        assert "You are a helpful AI assistant." in result["system"]
        # Should contain persona name
        assert "Zesty" in result["system"]

    def test_build_with_structured_context(self, sample_system_prompt, mock_persona, populated_session):
        """Test building prompt with structured context included."""
        builder = PromptBuilder(sample_system_prompt, mock_persona)
        _, session_id = populated_session

        result = builder.build(
            session_id,
            include_structured_context=True,
            show_history_tokens=False,
            compression_limit=10,
            only_current_history=False,
        )

        system_part = result["system"]

        # Should contain system prompt
        assert "You are a helpful AI assistant." in system_part

        # Should contain persona
        assert "Zesty" in system_part

        # Should contain structured context
        assert "Project: Weather Dashboard" in system_part
        assert "Task: Implement forecast feature" in system_part
        assert "Goals: Display 7-day forecast" in system_part
        assert "Pending: Fetch API data" in system_part
        assert "Topic: weather" in system_part

    def test_build_with_history(self, sample_system_prompt, mock_persona, populated_session):
        """Test building prompt with conversation history."""
        builder = PromptBuilder(sample_system_prompt, mock_persona)
        _, session_id = populated_session

        # Add a few more messages to ensure we have history
        manager = ConversationManager()
        # Reuse the existing session from fixture
        manager._sessions[session_id] = populated_session[0]._sessions[session_id]
        manager._history[session_id] = populated_session[0]._history[session_id]
        manager._structured_memory[session_id] = populated_session[0]._structured_memory[session_id]
        manager._memory[session_id] = populated_session[0]._memory[session_id]
        manager._topics[session_id] = populated_session[0]._topics[session_id]

        result = builder.build(
            session_id,
            include_structured_context=False,
            show_history_tokens=False,
            compression_limit=5,
            only_current_history=False,
        )

        system_part = result["system"]

        # Should contain conversation history markers
        assert "[USER]" in system_part
        assert "[ASSISTANT]" in system_part
        # Should contain our added messages
        assert "Hello, how are you?" in system_part
        assert "I'm doing well, thank you!" in system_part

    def test_build_with_compression(self, sample_system_prompt, mock_persona):
        """Test that history gets compressed when exceeding limit."""
        builder = PromptBuilder(sample_system_prompt, mock_persona)
        session_id = "compression_test"

        # Create manager and populate with many messages
        manager = ConversationManager()
        manager.start_session(session_id)

        # Add more than compression_limit (default 10) messages
        for i in range(15):
            manager.add_message(session_id, "user", f"User message {i}")
            manager.add_message(session_id, "assistant", f"Assistant response {i}")

        result = builder.build(
            session_id,
            include_structured_context=False,
            show_history_tokens=False,
            compression_limit=10,  # Should compress when > 10 messages
            only_current_history=False,
        )

        system_part = result["system"]

        # Should contain compression indicator
        assert "CONTINUED" in system_part
        # Should contain recent messages
        assert "User message 14" in system_part
        assert "Assistant response 14" in system_part
        # Should contain older messages in compressed section
        assert "User message 0" in system_part  # Still present in compressed part

    def test_build_user_section(self):
        """Test building the user message section."""
        builder = PromptBuilder("system prompt", {})
        user_msg = builder.build_user_section("What is the meaning of life?")

        assert user_msg["role"] == "user"
        assert user_msg["content"] == "What is the meaning of life?"

    def test_format_history_as_token_header(self):
        """Test the token header formatter."""
        test_str = "This is a test sentence with seven words."
        header = PromptBuilder.format_history_as_token_header(test_str)
        assert "<!-- history-tokens:7 -->" in header

        empty_header = PromptBuilder.format_history_as_token_header("")
        assert "<!-- history-tokens:0 -->" in empty_header

    def test_build_with_empty_session(self, sample_system_prompt, mock_persona):
        """Test building prompt for a session with no history."""
        builder = PromptBuilder(sample_system_prompt, mock_persona)
        session_id = "empty_session"

        # Create a fresh session
        manager = ConversationManager()
        manager.start_session(session_id)

        result = builder.build(
            session_id,
            include_structured_context=True,
            show_history_tokens=False,
            compression_limit=10,
            only_current_history=False,
        )

        system_part = result["system"]
        # Should contain system and persona
        assert "You are a helpful AI assistant." in system_part
        assert "Zesty" in system_part
        # Structured context should be empty
        # History should be empty
        # Should not crash or throw errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])