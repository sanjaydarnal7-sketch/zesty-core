"""
Zesty OS
Runtime Event Bus

Mission 85

Simple publish-subscribe event system.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable


class RuntimeEventBus:
    """Simple publish-subscribe event bus."""

    def __init__(self) -> None:
        self._subscribers = defaultdict(list)

    def subscribe(self, event: str, callback: Callable) -> None:
        """Register a callback for an event."""
        self._subscribers[event].append(callback)

    def publish(self, event: str, data=None) -> None:
        """Publish an event to all subscribers."""
        for callback in self._subscribers[event]:
            callback(data)


if __name__ == "__main__":

    print("===== ZESTY RUNTIME EVENT BUS =====")

    bus = RuntimeEventBus()

    def on_runtime_started(data):
        print("Runtime Started:", data)

    bus.subscribe("runtime.started", on_runtime_started)

    bus.publish(
        "runtime.started",
        {"status": "ready", "version": "1.0.0"},
    )