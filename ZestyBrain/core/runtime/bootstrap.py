"""
Zesty OS
Runtime Bootstrap

Mission 89

Initializes the runtime foundation.
"""

from __future__ import annotations

from core.runtime.lifecycle import RuntimeLifecycle, RuntimePhase
from core.runtime.config import RuntimeConfig
from core.runtime.state import RuntimeState


class RuntimeBootstrap:
    """Initializes the runtime."""

    def __init__(self) -> None:
        self.lifecycle = RuntimeLifecycle()
        self.config = RuntimeConfig()
        self.state = RuntimeState()

    def initialize(self) -> None:
        self.lifecycle.set_phase(RuntimePhase.STARTING)

        self.state.set("runtime_status", "running")

        print("Runtime initialized successfully.")

        self.lifecycle.set_phase(RuntimePhase.RUNNING)


if __name__ == "__main__":

    print("===== ZESTY RUNTIME BOOTSTRAP =====")

    runtime = RuntimeBootstrap()

    runtime.initialize()

    print("Lifecycle:", runtime.lifecycle.get_phase().value)
    print("Status:", runtime.state.get("runtime_status"))