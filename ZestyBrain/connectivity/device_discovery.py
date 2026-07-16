"""
Zesty OS
Device Discovery Engine
Version: 1.0

Mission 64

Discovers available devices and prepares
them for registration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DiscoveredDevice:
    """
    Represents a discovered device.
    """

    name: str
    device_type: str
    connection: str


class DeviceDiscovery:
    """
    Base device discovery engine.
    """

    def discover(self) -> list[DiscoveredDevice]:
        """
        Temporary mock discovery.

        Future versions will discover:
        - Wi-Fi devices
        - Bluetooth devices
        - USB devices
        """

        return [

            DiscoveredDevice(
                name="Chief's Phone",
                device_type="phone",
                connection="wifi",
            ),

            DiscoveredDevice(
                name="Bluetooth Headset",
                device_type="audio",
                connection="bluetooth",
            ),

            DiscoveredDevice(
                name="Laptop Webcam",
                device_type="camera",
                connection="internal",
            ),
        ]


# ---------------------------------------------------------
# Self Test
# ---------------------------------------------------------

if __name__ == "__main__":

    discovery = DeviceDiscovery()

    devices = discovery.discover()

    print("===== DEVICE DISCOVERY TEST =====")
    print()

    print("Devices Found :", len(devices))
    print()

    for device in devices:

        print(
            f"{device.name} | "
            f"{device.device_type} | "
            f"{device.connection}"
        )

    print()

    print("Mission 64 Passed")