"""
Zesty OS
Runtime Lifecycle Manager

Mission 88

Tracks the current runtime lifecycle stage.
"""

from __future__ import annotations

from enum import Enum


class RuntimePhase(Enum):
    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    STOPPING = "stopping"
    STOPPED = "stopped"


class RuntimeLifecycle:
    """Tracks runtime lifecycle."""

    def __init__(self) -> None:
        self._phase = RuntimePhase.INITIALIZING

    def set_phase(self, phase: RuntimePhase) -> None:
        self._phase = phase

    def get_phase(self) -> RuntimePhase:
        return self._phase


if __name__ == "__main__":

    print("===== ZESTY RUNTIME LIFECYCLE =====")

    lifecycle = RuntimeLifecycle()

    print("Current:", lifecycle.get_phase().value)

    lifecycle.set_phase(RuntimePhase.STARTING)
    print("Current:", lifecycle.get_phase().value)

    lifecycle.set_phase(RuntimePhase.RUNNING)
    print("Current:", lifecycle.get_phase().value)

    lifecycle.set_phase(RuntimePhase.STOPPING)
    print("Current:", lifecycle.get_phase().value)

    lifecycle.set_phase(RuntimePhase.STOPPED)
    print("Current:", lifecycle.get_phase().value)
