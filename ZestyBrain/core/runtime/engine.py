"""
Zesty OS
Runtime Engine

Mission 92

Base interface for all runtime engines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.runtime.context import RuntimeContext


class RuntimeEngine(ABC):
    """Base class for all Zesty runtime engines."""

    def __init__(self, context: RuntimeContext) -> None:
        self.context = context

    @abstractmethod
    def initialize(self) -> None:
        """Prepare the engine."""

    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully stop the engine."""


class DemoEngine(RuntimeEngine):
    """Simple demo implementation."""

    def initialize(self) -> None:
        self.context.state.set("demo_engine", "initialized")
        print("Demo Engine Initialized")

    def shutdown(self) -> None:
        self.context.state.set("demo_engine", "stopped")
        print("Demo Engine Stopped")


if __name__ == "__main__":

    print("===== ZESTY RUNTIME ENGINE =====")

    context = RuntimeContext()

    engine = DemoEngine(context)

    engine.initialize()

    print(
        "State:",
        context.state.get("demo_engine"),
    )

    engine.shutdown()

    print(
        "State:",
        context.state.get("demo_engine"),
    )