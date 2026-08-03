"""Unit tests for the Working Memory Engine."""

import pytest
import datetime as _dt
from unittest.mock import patch

from conversation.state import WorkingMemoryState
from conversation.working_memory import WorkingMemoryEngine


# ---------------------------------------------------------------------------
# WorkingMemoryState tests
# ---------------------------------------------------------------------------
class TestWorkingMemoryState:
    """Tests for the WorkingMemoryState dataclass."""

    def test_default_initialization(self):
        """All fields should default to None or empty collections."""
        state = WorkingMemoryState()
        assert state.current_topic is None
        assert state.active_project is None
        assert state.current_goal is None
        assert state.pending_tasks == []
        assert state.open_questions == []
        assert state.user_intent is None
        assert state.recent_decisions == []
        assert state.active_file is None
        assert state.current_mode is None
        assert state.metadata == {}
        assert state.expires_at is None

    def test_touch_updates_timestamp(self):
        """touch() should update updated_at."""
        state = WorkingMemoryState()
        original = state.updated_at
        # Sleep a tiny bit to ensure timestamp changes
        import time
        time.sleep(0.001)
        state.touch()
        assert state.updated_at > original

    def test_is_expired_never_expires_by_default(self):
        """Without an expiration set, is_expired() should return False."""
        state = WorkingMemoryState()
        assert state.is_expired() is False

    def test_is_expired_with_ttl(self):
        """State should be expired after its TTL passes."""
        state = WorkingMemoryState()
        state.set_expiration(1)  # 1 second TTL
        assert state.is_expired() is False
        # Simulate time passing
        future = _dt.datetime.utcnow() + _dt.timedelta(seconds=2)
        assert state.is_expired(now=future) is True

    def test_set_expiration(self):
        """set_expiration should set expires_at to now + ttl."""
        state = WorkingMemoryState()
        before = _dt.datetime.utcnow()
        state.set_expiration(60)
        after = _dt.datetime.utcnow()
        assert state.expires_at is not None
        assert before + _dt.timedelta(seconds=60) <= state.expires_at
        assert state.expires_at <= after + _dt.timedelta(seconds=60)

    def test_set_expiration_negative_raises(self):
        """Negative TTL should raise ValueError."""
        state = WorkingMemoryState()
        with pytest.raises(ValueError, match="non-negative"):
            state.set_expiration(-1)

    def test_clear_expiration(self):
        """clear_expiration should remove the expiration."""
        state = WorkingMemoryState()
        state.set_expiration(60)
        assert state.expires_at is not None
        state.clear_expiration()
        assert state.expires_at is None

    def test_to_dict(self):
        """to_dict should produce a JSON-serializable dict."""
        state = WorkingMemoryState()
        state.current_topic = "coding"
        state.active_project = "zesty"
        state.pending_tasks = ["task1", "task2"]
        state.set_expiration(300)

        d = state.to_dict()
        assert d["current_topic"] == "coding"
        assert d["active_project"] == "zesty"
        assert d["pending_tasks"] == ["task1", "task2"]
        assert d["expires_at"] is not None
        assert "created_at" in d
        assert "updated_at" in d

    def test_from_dict(self):
        """from_dict should reconstruct a state from a dict."""
        original = WorkingMemoryState()
        original.current_topic = "planning"
        original.current_mode = "review"
        original.pending_tasks = ["task1"]
        original.set_expiration(120)

        d = original.to_dict()
        reconstructed = WorkingMemoryState.from_dict(d)
        assert reconstructed.current_topic == "planning"
        assert reconstructed.current_mode == "review"
        assert reconstructed.pending_tasks == ["task1"]
        assert reconstructed.expires_at == original.expires_at

    def test_export_for_prompt_empty(self):
        """Empty state should export as empty string."""
        state = WorkingMemoryState()
        assert state.export_for_prompt() == ""

    def test_export_for_prompt_populated(self):
        """Populated state should export with all non-empty fields."""
        state = WorkingMemoryState()
        state.current_topic = "coding"
        state.active_project = "zesty"
        state.current_goal = "build API"
        state.pending_tasks = ["task1", "task2"]
        state.open_questions = ["Q1"]
        state.user_intent = "help"
        state.recent_decisions = ["decided A"]
        state.active_file = "main.py"
        state.current_mode = "coding"

        result = state.export_for_prompt()
        assert "Topic: coding" in result
        assert "Project: zesty" in result
        assert "Goal: build API" in result
        assert "Pending: task1, task2" in result
        assert "Questions: Q1" in result
        assert "Intent: help" in result
        assert "Decisions: decided A" in result
        assert "File: main.py" in result
        assert "Mode: coding" in result

    def test_export_for_prompt_partial(self):
        """Only non-empty fields should be in the export."""
        state = WorkingMemoryState()
        state.current_topic = "coding"
        state.current_mode = "review"

        result = state.export_for_prompt()
        assert "Topic: coding" in result
        assert "Mode: review" in result
        assert "Project:" not in result
        assert "Goal:" not in result


# ---------------------------------------------------------------------------
# WorkingMemoryEngine tests
# ---------------------------------------------------------------------------
class TestWorkingMemoryEngine:
    """Tests for the WorkingMemoryEngine class."""

    def test_create_session(self):
        """create_session should return a valid state."""
        engine = WorkingMemoryEngine()
        state = engine.create_session("session-1")
        assert isinstance(state, WorkingMemoryState)
        assert engine.has_session("session-1")

    def test_create_session_duplicate_raises(self):
        """Creating a duplicate session should raise ValueError."""
        engine = WorkingMemoryEngine()
        engine.create_session("session-1")
        with pytest.raises(ValueError, match="already exists"):
            engine.create_session("session-1")

    def test_get_session(self):
        """get_session should return the state for an existing session."""
        engine = WorkingMemoryEngine()
        engine.create_session("session-1")
        state = engine.get_session("session-1")
        assert isinstance(state, WorkingMemoryState)

    def test_get_session_missing_raises(self):
        """get_session should raise KeyError for non-existent session."""
        engine = WorkingMemoryEngine()
        with pytest.raises(KeyError, match="does not exist"):
            engine.get_session("nonexistent")

    def test_has_session(self):
        """has_session should return True/False correctly."""
        engine = WorkingMemoryEngine()
        assert engine.has_session("session-1") is False
        engine.create_session("session-1")
        assert engine.has_session("session-1") is True

    def test_delete_session(self):
        """delete_session should remove the session."""
        engine = WorkingMemoryEngine()
        engine.create_session("session-1")
        assert engine.delete_session("session-1") is True
        assert engine.has_session("session-1") is False

    def test_delete_session_missing_returns_false(self):
        """delete_session should return False for non-existent session."""
        engine = WorkingMemoryEngine()
        assert engine.delete_session("nonexistent") is False

    def test_reset_session(self):
        """reset_session should clear state but keep the session."""
        engine = WorkingMemoryEngine()
        state = engine.create_session("session-1")
        state.current_topic = "coding"
        state.pending_tasks = ["task1"]

        new_state = engine.reset_session("session-1")
        assert new_state.current_topic is None
        assert new_state.pending_tasks == []
        assert engine.has_session("session-1")  # Session still exists

    def test_reset_session_missing_raises(self):
        """reset_session should raise KeyError for non-existent session."""
        engine = WorkingMemoryEngine()
        with pytest.raises(KeyError, match="does not exist"):
            engine.reset_session("nonexistent")

    def test_clear_all_sessions(self):
        """clear_all_sessions should remove all sessions."""
        engine = WorkingMemoryEngine()
        engine.create_session("s1")
        engine.create_session("s2")
        count = engine.clear_all_sessions()
        assert count == 2
        assert engine.list_sessions() == []

    def test_list_sessions(self):
        """list_sessions should return all session IDs."""
        engine = WorkingMemoryEngine()
        engine.create_session("s1")
        engine.create_session("s2")
        assert sorted(engine.list_sessions()) == ["s1", "s2"]

    def test_cleanup_expired(self):
        """cleanup_expired should remove only expired sessions."""
        engine = WorkingMemoryEngine()
        engine.create_session("active", ttl_seconds=3600)
        engine.create_session("expired", ttl_seconds=1)

        # Simulate time passing for the expired session
        future = _dt.datetime.utcnow() + _dt.timedelta(seconds=2)
        with patch("conversation.state._dt.datetime") as mock_dt:
            mock_dt.utcnow.return_value = future
            mock_dt.timedelta = _dt.timedelta
            count = engine.cleanup_expired()

        assert count == 1
        assert engine.has_session("active")
        assert not engine.has_session("expired")

    def test_default_ttl(self):
        """Sessions should use the engine's default TTL."""
        engine = WorkingMemoryEngine(default_ttl_seconds=60)
        state = engine.create_session("session-1")
        assert state.expires_at is not None

    def test_custom_ttl_overrides_default(self):
        """Session-specific TTL should override the engine default."""
        engine = WorkingMemoryEngine(default_ttl_seconds=60)
        state = engine.create_session("session-1", ttl_seconds=120)
        assert state.expires_at is not None
        # Verify it's approximately 120 seconds from now, not 60
        now = _dt.datetime.utcnow()
        expected = now + _dt.timedelta(seconds=120)
        assert abs((state.expires_at - expected).total_seconds()) < 1

    def test_initial_state(self):
        """create_session should accept initial state values."""
        engine = WorkingMemoryEngine()
        initial = {
            "current_topic": "planning",
            "active_project": "zesty",
            "pending_tasks": ["task1"],
        }
        state = engine.create_session("session-1", initial_state=initial)
        assert state.current_topic == "planning"
        assert state.active_project == "zesty"
        assert state.pending_tasks == ["task1"]

    def test_is_expired(self):
        """is_expired should return the session's expiration status."""
        engine = WorkingMemoryEngine()
        engine.create_session("active", ttl_seconds=3600)
        assert engine.is_expired("active") is False

    def test_is_expired_missing_raises(self):
        """is_expired should raise KeyError for non-existent session."""
        engine = WorkingMemoryEngine()
        with pytest.raises(KeyError, match="does not exist"):
            engine.is_expired("nonexistent")

    def test_set_expiration(self):
        """set_expiration should update the session's TTL."""
        engine = WorkingMemoryEngine()
        engine.create_session("session-1")
        engine.set_expiration("session-1", 300)
        state = engine.get_session("session-1")
        assert state.expires_at is not None

    def test_set_expiration_missing_raises(self):
        """set_expiration should raise KeyError for non-existent session."""
        engine = WorkingMemoryEngine()
        with pytest.raises(KeyError, match="does not exist"):
            engine.set_expiration("nonexistent", 300)

    def test_clear_expiration(self):
        """clear_expiration should remove the session's TTL."""
        engine = WorkingMemoryEngine()
        engine.create_session("session-1", ttl_seconds=300)
        engine.clear_expiration("session-1")
        state = engine.get_session("session-1")
        assert state.expires_at is None

    def test_clear_expiration_missing_raises(self):
        """clear_expiration should raise KeyError for non-existent session."""
        engine = WorkingMemoryEngine()
        with pytest.raises(KeyError, match="does not exist"):
            engine.clear_expiration("nonexistent")


# ---------------------------------------------------------------------------
# State mutator tests
# ---------------------------------------------------------------------------
class TestStateMutators:
    """Tests for state mutation methods."""

    def setup_method(self):
        self.engine = WorkingMemoryEngine()
        self.engine.create_session("session-1")

    def test_set_current_topic(self):
        self.engine.set_current_topic("session-1", "coding")
        assert self.engine.get_session("session-1").current_topic == "coding"

    def test_set_active_project(self):
        self.engine.set_active_project("session-1", "zesty")
        assert self.engine.get_session("session-1").active_project == "zesty"

    def test_set_current_goal(self):
        self.engine.set_current_goal("session-1", "build API")
        assert self.engine.get_session("session-1").current_goal == "build API"

    def test_set_user_intent(self):
        self.engine.set_user_intent("session-1", "help")
        assert self.engine.get_session("session-1").user_intent == "help"

    def test_set_active_file(self):
        self.engine.set_active_file("session-1", "main.py")
        assert self.engine.get_session("session-1").active_file == "main.py"

    def test_set_current_mode(self):
        self.engine.set_current_mode("session-1", "coding")
        assert self.engine.get_session("session-1").current_mode == "coding"

    def test_set_topic_none(self):
        self.engine.set_current_topic("session-1", "coding")
        self.engine.set_current_topic("session-1", None)
        assert self.engine.get_session("session-1").current_topic is None

    def test_mutator_missing_raises(self):
        """All mutators should raise KeyError for non-existent sessions."""
        with pytest.raises(KeyError):
            self.engine.set_current_topic("nonexistent", "test")
        with pytest.raises(KeyError):
            self.engine.set_active_project("nonexistent", "test")
        with pytest.raises(KeyError):
            self.engine.set_current_goal("nonexistent", "test")
        with pytest.raises(KeyError):
            self.engine.set_user_intent("nonexistent", "test")
        with pytest.raises(KeyError):
            self.engine.set_active_file("nonexistent", "test")
        with pytest.raises(KeyError):
            self.engine.set_current_mode("nonexistent", "test")


# ---------------------------------------------------------------------------
# List-based field operation tests
# ---------------------------------------------------------------------------
class TestListOperations:
    """Tests for list-based field operations."""

    def setup_method(self):
        self.engine = WorkingMemoryEngine()
        self.engine.create_session("session-1")

    def test_add_pending_task(self):
        self.engine.add_pending_task("session-1", "task1")
        assert "task1" in self.engine.get_session("session-1").pending_tasks

    def test_add_duplicate_pending_task(self):
        self.engine.add_pending_task("session-1", "task1")
        self.engine.add_pending_task("session-1", "task1")
        assert len(self.engine.get_session("session-1").pending_tasks) == 1

    def test_add_empty_pending_task(self):
        self.engine.add_pending_task("session-1", "")
        assert len(self.engine.get_session("session-1").pending_tasks) == 0

    def test_remove_pending_task(self):
        self.engine.add_pending_task("session-1", "task1")
        assert self.engine.remove_pending_task("session-1", "task1") is True
        assert "task1" not in self.engine.get_session("session-1").pending_tasks

    def test_remove_nonexistent_pending_task(self):
        assert self.engine.remove_pending_task("session-1", "task1") is False

    def test_add_open_question(self):
        self.engine.add_open_question("session-1", "What is the meaning?")
        assert "What is the meaning?" in self.engine.get_session("session-1").open_questions

    def test_add_duplicate_open_question(self):
        self.engine.add_open_question("session-1", "Q1")
        self.engine.add_open_question("session-1", "Q1")
        assert len(self.engine.get_session("session-1").open_questions) == 1

    def test_remove_open_question(self):
        self.engine.add_open_question("session-1", "Q1")
        assert self.engine.remove_open_question("session-1", "Q1") is True
        assert "Q1" not in self.engine.get_session("session-1").open_questions

    def test_remove_nonexistent_open_question(self):
        assert self.engine.remove_open_question("session-1", "Q1") is False

    def test_add_recent_decision(self):
        self.engine.add_recent_decision("session-1", "decided A")
        assert "decided A" in self.engine.get_session("session-1").recent_decisions

    def test_add_empty_recent_decision(self):
        self.engine.add_recent_decision("session-1", "")
        assert len(self.engine.get_session("session-1").recent_decisions) == 0

    def test_get_recent_decisions_no_limit(self):
        self.engine.add_recent_decision("session-1", "dec1")
        self.engine.add_recent_decision("session-1", "dec2")
        decisions = self.engine.get_recent_decisions("session-1")
        assert decisions == ["dec1", "dec2"]

    def test_get_recent_decisions_with_limit(self):
        self.engine.add_recent_decision("session-1", "dec1")
        self.engine.add_recent_decision("session-1", "dec2")
        self.engine.add_recent_decision("session-1", "dec3")
        decisions = self.engine.get_recent_decisions("session-1", limit=2)
        assert decisions == ["dec2", "dec3"]

    def test_list_ops_missing_raises(self):
        """All list operations should raise KeyError for non-existent sessions."""
        with pytest.raises(KeyError):
            self.engine.add_pending_task("nonexistent", "task1")
        with pytest.raises(KeyError):
            self.engine.remove_pending_task("nonexistent", "task1")
        with pytest.raises(KeyError):
            self.engine.add_open_question("nonexistent", "Q1")
        with pytest.raises(KeyError):
            self.engine.remove_open_question("nonexistent", "Q1")
        with pytest.raises(KeyError):
            self.engine.add_recent_decision("nonexistent", "dec1")
        with pytest.raises(KeyError):
            self.engine.get_recent_decisions("nonexistent")


# ---------------------------------------------------------------------------
# Export tests
# ---------------------------------------------------------------------------
class TestExport:
    """Tests for export methods."""

    def test_export_for_prompt(self):
        engine = WorkingMemoryEngine()
        state = engine.create_session("session-1")
        state.current_topic = "coding"
        state.active_project = "zesty"
        state.current_mode = "review"

        result = engine.export_for_prompt("session-1")
        assert "Topic: coding" in result
        assert "Project: zesty" in result
        assert "Mode: review" in result

    def test_export_for_prompt_empty(self):
        engine = WorkingMemoryEngine()
        engine.create_session("session-1")
        result = engine.export_for_prompt("session-1")
        assert result == ""

    def test_export_for_prompt_missing_raises(self):
        engine = WorkingMemoryEngine()
        with pytest.raises(KeyError, match="does not exist"):
            engine.export_for_prompt("nonexistent")

    def test_export_as_dict(self):
        engine = WorkingMemoryEngine()
        state = engine.create_session("session-1")
        state.current_topic = "coding"
        state.pending_tasks = ["task1"]

        d = engine.export_as_dict("session-1")
        assert d["current_topic"] == "coding"
        assert d["pending_tasks"] == ["task1"]
        assert "created_at" in d
        assert "updated_at" in d

    def test_export_as_dict_missing_raises(self):
        engine = WorkingMemoryEngine()
        with pytest.raises(KeyError, match="does not exist"):
            engine.export_as_dict("nonexistent")


# ---------------------------------------------------------------------------
# Thread safety tests
# ---------------------------------------------------------------------------
class TestThreadSafety:
    """Tests to verify thread safety of the engine."""

    def test_concurrent_session_creation(self):
        """Multiple threads should be able to create sessions concurrently."""
        import threading

        engine = WorkingMemoryEngine()
        errors = []

        def create_session(sid):
            try:
                engine.create_session(sid)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(10):
            t = threading.Thread(target=create_session, args=(f"session-{i}",))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(engine.list_sessions()) == 10

    def test_concurrent_state_updates(self):
        """Multiple threads should be able to update state concurrently."""
        import threading

        engine = WorkingMemoryEngine()
        engine.create_session("session-1")

        def add_task(task):
            engine.add_pending_task("session-1", task)

        threads = []
        for i in range(10):
            t = threading.Thread(target=add_task, args=(f"task-{i}",))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        state = engine.get_session("session-1")
        assert len(state.pending_tasks) == 10
