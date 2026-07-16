"""
Zesty OS
Device Registry
Version: 1.0

Mission 63

Stores and manages all connected devices.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(slots=True)
class DeviceInfo:
    """
    Information about a connected device.
    """

    device_id: str
    name: str
    device_type: str
    connection: str
    trusted: bool = False
    connected: bool = True
    last_seen: datetime | None = None

    def touch(self) -> None:

        self.last_seen = datetime.now(timezone.utc)


class DeviceRegistry:
    """
    Registry of connected devices.
    """

    def __init__(self):

        self._devices: dict[str, DeviceInfo] = {}

    def register(
        self,
        device: DeviceInfo,
    ) -> None:

        device.touch()

        self._devices[device.device_id] = device

    def unregister(
        self,
        device_id: str,
    ) -> None:

        self._devices.pop(device_id, None)

    def get(
        self,
        device_id: str,
    ) -> DeviceInfo | None:

        return self._devices.get(device_id)

    def exists(
        self,
        device_id: str,
    ) -> bool:

        return device_id in self._devices

    def list_devices(self) -> list[DeviceInfo]:

        return sorted(
            self._devices.values(),
            key=lambda device: device.name.lower(),
        )

    def count(self) -> int:

        return len(self._devices)


# ---------------------------------------------------------
# Self Test
# ---------------------------------------------------------

if __name__ == "__main__":

    registry = DeviceRegistry()

    phone = DeviceInfo(
        device_id="phone001",
        name="Chief's Phone",
        device_type="phone",
        connection="wifi",
        trusted=True,
    )

    headset = DeviceInfo(
        device_id="headset001",
        name="Bluetooth Headset",
        device_type="audio",
        connection="bluetooth",
    )

    registry.register(phone)
    registry.register(headset)

    print("===== DEVICE REGISTRY TEST =====")
    print()

    print("Devices :", registry.count())

    print()

    for device in registry.list_devices():

        print(
            f"{device.name} | "
            f"{device.device_type} | "
            f"{device.connection} | "
            f"Trusted={device.trusted}"
        )

    print()

    print("Mission 63 Passed")