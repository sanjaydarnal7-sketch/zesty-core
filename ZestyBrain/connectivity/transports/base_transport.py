"""
Zesty OS
Base Transport Framework
Version: 1.0

Mission 67

Defines the communication interface used by
all transport implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class TransportInfo:
    """
    Information describing a transport.
    """

    name: str
    protocol: str
    connected: bool = False


class BaseTransport(ABC):
    """
    Base class for every transport layer.
    """

    def __init__(
        self,
        name: str,
        protocol: str,
    ):

        self.info = TransportInfo(
            name=name,
            protocol=protocol,
        )

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection.
        """

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection.
        """

    @abstractmethod
    def send(
        self,
        payload: bytes,
    ) -> bool:
        """
        Send bytes.
        """

    @abstractmethod
    def receive(self) -> bytes:
        """
        Receive bytes.
        """

    def status(self) -> str:

        return (
            "Connected"
            if self.info.connected
            else "Disconnected"
        )


# ---------------------------------------------------------
# Demo Transport
# ---------------------------------------------------------

class DemoTransport(BaseTransport):

    def __init__(self):

        super().__init__(
            name="Demo Transport",
            protocol="demo",
        )

    def connect(self):

        self.info.connected = True

        return True

    def disconnect(self):

        self.info.connected = False

        return True

    def send(
        self,
        payload: bytes,
    ):

        if not self.info.connected:

            return False

        self._buffer = payload

        return True

    def receive(self):

        return getattr(
            self,
            "_buffer",
            b"",
        )


# ---------------------------------------------------------
# Self Test
# ---------------------------------------------------------

if __name__ == "__main__":

    transport = DemoTransport()

    print("===== BASE TRANSPORT TEST =====")
    print()

    transport.connect()

    print("Status :", transport.status())

    transport.send(b"Hello Zesty")

    print("Received :", transport.receive().decode())

    transport.disconnect()

    print("Disconnected :", transport.status())

    print()

    print("Mission 67 Passed")