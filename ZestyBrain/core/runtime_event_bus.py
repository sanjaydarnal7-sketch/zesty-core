"""
Zesty OS
Runtime Event Bus
Version: 1.0

Mission 65

Provides event-based communication between
independent Zesty modules.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass(slots=True)
class RuntimeEvent:
    """
    Standard runtime event.
    """

    name: str
    source: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class RuntimeEventBus:
    """
    Simple publish / subscribe event bus.
    """

    def __init__(self):

        self._subscribers: dict[
            str,
            list[Callable[[RuntimeEvent], None]]
        ] = defaultdict(list)

    def subscribe(
        self,
        event_name: str,
        callback: Callable[[RuntimeEvent], None],
    ) -> None:

        self._subscribers[event_name].append(callback)

    def unsubscribe(
        self,
        event_name: str,
        callback: Callable[[RuntimeEvent], None],
    ) -> None:

        if callback in self._subscribers[event_name]:

            self._subscribers[event_name].remove(callback)

    def publish(
        self,
        event: RuntimeEvent,
    ) -> None:

        for callback in self._subscribers.get(
            event.name,
            [],
        ):

            callback(event)

    def subscriber_count(
        self,
        event_name: str,
    ) -> int:

        return len(
            self._subscribers.get(
                event_name,
                [],
            )
        )


# ---------------------------------------------------------
# Self Test
# ---------------------------------------------------------

if __name__ == "__main__":

    bus = RuntimeEventBus()

    def guardian_listener(event: RuntimeEvent):

        print(
            f"[Guardian] {event.name} "
            f"from {event.source}"
        )

    def logger_listener(event: RuntimeEvent):

        print(
            f"[Logger] {event.name}"
        )

    bus.subscribe(
        "DEVICE_CONNECTED",
        guardian_listener,
    )

    bus.subscribe(
        "DEVICE_CONNECTED",
        logger_listener,
    )

    event = RuntimeEvent(

        name="DEVICE_CONNECTED",

        source="DeviceDiscovery",

        data={
            "device": "Chief's Phone"
        },
    )

    print("===== RUNTIME EVENT BUS TEST =====")
    print()

    bus.publish(event)

    print()

    print(
        "Subscribers:",
        bus.subscriber_count(
            "DEVICE_CONNECTED"
        )
    )

    print()

    print("Mission 65 Passed")