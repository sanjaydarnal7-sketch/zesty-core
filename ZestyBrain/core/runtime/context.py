"""
Zesty OS
Runtime Context

Mission 91

Shared runtime context for all core engines.
"""

from __future__ import annotations

from core.runtime.config import RuntimeConfig
from core.runtime.state import RuntimeState
from core.runtime.lifecycle import RuntimeLifecycle
from core.runtime.event_bus import RuntimeEventBus


class RuntimeContext:
    """Shared runtime context."""

    def __init__(self) -> None:
        self.config = RuntimeConfig()
        self.state = RuntimeState()
        self.lifecycle = RuntimeLifecycle()
        self.events = RuntimeEventBus()


if __name__ == "__main__":

    print("===== ZESTY RUNTIME CONTEXT =====")

    context = RuntimeContext()

    context.state.set("runtime_status", "running")

    print("Status:", context.state.get("runtime_status"))
    print("Provider:", context.config.get("default_provider"))
    print("Phase:", context.lifecycle.get_phase().value)