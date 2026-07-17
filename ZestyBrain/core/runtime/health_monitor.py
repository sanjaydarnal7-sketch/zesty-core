"""
Zesty OS
Runtime Health Monitor

Mission 77

Monitors runtime services.
"""

from __future__ import annotations

from typing import Any


class RuntimeHealthMonitor:

    def __init__(self):
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service

    def report(self) -> dict[str, dict]:

        report = {}

        for name, service in self._services.items():

            healthy = False

            state = "unknown"

            if hasattr(service, "health_check"):
                try:
                    healthy = bool(service.health_check())
                except Exception:
                    healthy = False

            if hasattr(service, "status"):
                try:
                    state = service.status()
                except Exception:
                    state = "unknown"

            report[name] = {
                "healthy": healthy,
                "state": state,
            }

        return report


if __name__ == "__main__":

    print("Runtime Health Monitor Ready")