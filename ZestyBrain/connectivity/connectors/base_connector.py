"""
Zesty OS
Universal Device Connector
Version: 1.0

Mission 66

Defines the standard interface for all
hardware connectors.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(slots=True)
class ConnectorCapabilities:
    """
    Describes the capabilities supported
    by a connector.
    """

    camera: bool = False
    microphone: bool = False
    speaker: bool = False
    storage: bool = False
    gps: bool = False
    notifications: bool = False
    network: bool = False
    custom: dict[str, bool] = field(default_factory=dict)


class BaseConnector(ABC):
    """
    Base interface for every Zesty connector.
    """

    def __init__(
        self,
        connector_id: str,
        name: str,
    ):

        self.connector_id = connector_id
        self.name = name
        self.connected = False

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the hardware.
        """

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the hardware.
        """

    @abstractmethod
    def status(self) -> str:
        """
        Current connection status.
        """

    @abstractmethod
    def capabilities(self) -> ConnectorCapabilities:
        """
        Returns supported capabilities.
        """


# ---------------------------------------------------------
# Demo Connector
# ---------------------------------------------------------

class DemoPhoneConnector(BaseConnector):

    def connect(self):

        self.connected = True

        return True

    def disconnect(self):

        self.connected = False

        return True

    def status(self):

        return (
            "Connected"
            if self.connected
            else "Disconnected"
        )

    def capabilities(self):

        return ConnectorCapabilities(

            camera=True,

            microphone=True,

            speaker=True,

            storage=True,

            gps=True,

            notifications=True,

            network=True,
        )


# ---------------------------------------------------------
# Self Test
# ---------------------------------------------------------

if __name__ == "__main__":

    connector = DemoPhoneConnector(

        connector_id="phone001",

        name="Chief's Phone",

    )

    print("===== UDC TEST =====")
    print()

    connector.connect()

    print("Status :", connector.status())

    caps = connector.capabilities()

    print()

    print("Camera :", caps.camera)
    print("Microphone :", caps.microphone)
    print("Speaker :", caps.speaker)
    print("GPS :", caps.gps)
    print("Storage :", caps.storage)

    connector.disconnect()

    print()

    print("Disconnected :", connector.status())

    print()

    print("Mission 66 Passed")