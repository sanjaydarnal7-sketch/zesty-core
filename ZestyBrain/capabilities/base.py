"""
Zesty OS
Capability Base
Version: 1.1

Mission 47

Defines the standard interface that every
Jessie Capability must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CapabilityMetadata:
    """Describes a capability."""

    name: str
    version: str
    description: str

    author: str = "Jessie OS"

    category: str = "General"

    risk_level: str = "low"

    requires_network: bool = False

    requires_confirmation: bool = False

    supported_frameworks: list[str] = field(default_factory=list)

    supported_modes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CapabilityRequest:
    """Input passed to a capability."""

    capability: str

    payload: dict[str, Any]


@dataclass(slots=True)
class CapabilityResponse:
    """Standard capability response."""

    success: bool

    message: str

    data: Any | None = None


class BaseCapability(ABC):
    """
    Base class that every capability must inherit.
    """

    metadata: CapabilityMetadata

    @abstractmethod
    def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResponse:
        """
        Execute the capability.
        """
        raise NotImplementedError


if __name__ == "__main__":

    metadata = CapabilityMetadata(
        name="Demo Capability",
        version="1.0",
        description="Capability Base Self Test"
    )

    request = CapabilityRequest(
        capability="demo",
        payload={"message": "Hello Jessie"}
    )

    response = CapabilityResponse(
        success=True,
        message="Capability Base Loaded Successfully"
    )

    print("===== CAPABILITY BASE TEST =====")
    print()
    print(metadata)
    print()
    print(request)
    print()
    print(response)