"""
Zesty OS
Runtime Bootstrap

Mission 89

Initializes the runtime foundation.
"""

from __future__ import annotations

from core.runtime.manager import RuntimeManager


class RuntimeBootstrap:
    """Create and initialize the canonical Zesty OS runtime."""

    def __init__(self, runtime_manager: RuntimeManager | None = None) -> None:
        """Create the runtime manager before exposing runtime dependencies."""
        self.runtime_manager = runtime_manager or RuntimeManager()
        self.lifecycle = self.runtime_manager.lifecycle
        self.config = self.runtime_manager.runtime_config
        self.state = self.runtime_manager.state

    def initialize(self) -> None:
        """Initialize the runtime through its canonical coordinator."""
        self.runtime_manager.initialize()
        print("Runtime initialized successfully.")

    def shutdown(self) -> None:
        """Shut down the canonical runtime coordinator."""
        self.runtime_manager.shutdown()


if __name__ == "__main__":

    print("===== ZESTY RUNTIME BOOTSTRAP =====")

    runtime = RuntimeBootstrap()

    runtime.initialize()

    print("Lifecycle:", runtime.lifecycle.get_phase().value)
    print("Status:", runtime.state.get("runtime_status"))
