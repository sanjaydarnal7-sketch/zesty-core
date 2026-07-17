"""
Zesty OS
Runtime Scheduler

Mission 86

Simple task scheduler for runtime jobs.
"""

from __future__ import annotations

from typing import Callable


class RuntimeScheduler:
    """Stores and executes scheduled runtime tasks."""

    def __init__(self) -> None:
        self._tasks: list[tuple[str, Callable]] = []

    def register(self, name: str, task: Callable) -> None:
        """Register a task."""
        self._tasks.append((name, task))

    def run_all(self) -> None:
        """Run all registered tasks."""
        for name, task in self._tasks:
            print(f"Running task: {name}")
            task()


if __name__ == "__main__":

    print("===== ZESTY RUNTIME SCHEDULER =====")

    scheduler = RuntimeScheduler()

    def health_check():
        print("Health check completed.")

    def cleanup():
        print("Cleanup completed.")

    scheduler.register("health_check", health_check)
    scheduler.register("cleanup", cleanup)

    scheduler.run_all()