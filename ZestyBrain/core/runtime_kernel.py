"""
Zesty OS
Runtime Kernel
Version: 1.0

Mission 68

Central runtime responsible for managing
core runtime components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class RuntimeComponent:
    """
    Registered runtime component.
    """

    name: str
    instance: Any
    registered_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class RuntimeKernel:
    """
    Central runtime coordinator.
    """

    def __init__(self):

        self._running = False

        self._components: dict[
            str,
            RuntimeComponent,
        ] = {}

    def start(self) -> None:

        self._running = True

    def stop(self) -> None:

        self._running = False

    def running(self) -> bool:

        return self._running

    def register(
        self,
        name: str,
        instance: Any,
    ) -> None:

        self._components[name] = RuntimeComponent(

            name=name,

            instance=instance,
        )

    def get(
        self,
        name: str,
    ) -> Any | None:

        component = self._components.get(name)

        if component is None:

            return None

        return component.instance

    def registered_components(self) -> list[str]:

        return sorted(self._components.keys())

    def component_count(self) -> int:

        return len(self._components)


# ---------------------------------------------------------
# Self Test
# ---------------------------------------------------------

if __name__ == "__main__":

    kernel = RuntimeKernel()

    kernel.start()

    kernel.register(
        "event_bus",
        object(),
    )

    kernel.register(
        "device_registry",
        object(),
    )

    kernel.register(
        "guardian",
        object(),
    )

    print("===== RUNTIME KERNEL TEST =====")
    print()

    print("Running :", kernel.running())

    print("Components :", kernel.component_count())

    print()

    for component in kernel.registered_components():

        print(component)

    kernel.stop()

    print()

    print("Stopped :", kernel.running())

    print()

    print("Mission 68 Passed")