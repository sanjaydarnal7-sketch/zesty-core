"""Focused integration checks for canonical runtime initialization."""

from core.runtime.bootstrap import RuntimeBootstrap
from core.runtime.lifecycle import RuntimePhase
from core.runtime.manager import RuntimeManager


def test_bootstrap_creates_and_initializes_runtime_manager() -> None:
    """The bootstrap must expose a running canonical runtime manager."""
    bootstrap = RuntimeBootstrap()

    assert isinstance(bootstrap.runtime_manager, RuntimeManager)
    assert bootstrap.runtime_manager.initialized is False

    bootstrap.initialize()

    assert bootstrap.runtime_manager.initialized is True
    assert bootstrap.lifecycle.get_phase() is RuntimePhase.RUNNING
    assert bootstrap.state.get("runtime_status") == "running"

    bootstrap.shutdown()

    assert bootstrap.lifecycle.get_phase() is RuntimePhase.STOPPED
    assert bootstrap.state.get("runtime_status") == "stopped"
