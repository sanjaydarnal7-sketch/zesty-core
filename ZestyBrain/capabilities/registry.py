"""
Zesty OS
Capability Registry
Version: 1.0

Mission 48

Central registry for all Jessie capabilities.
"""

from __future__ import annotations

from typing import Dict

from capabilities.base import BaseCapability


class CapabilityRegistry:
    """
    Stores every available capability.
    """

    def __init__(self):

        self._capabilities: Dict[str, BaseCapability] = {}

    def register(
        self,
        capability: BaseCapability
    ) -> None:

        name = capability.metadata.name.lower()

        if name in self._capabilities:
            raise ValueError(
                f"Capability '{name}' is already registered."
            )

        self._capabilities[name] = capability

    def unregister(
        self,
        name: str
    ) -> None:

        self._capabilities.pop(name.lower(), None)

    def get(
        self,
        name: str
    ) -> BaseCapability | None:

        return self._capabilities.get(name.lower())

    def exists(
        self,
        name: str
    ) -> bool:

        return name.lower() in self._capabilities

    def list_all(self) -> list[str]:

        return sorted(self._capabilities.keys())

    def count(self) -> int:

        return len(self._capabilities)


if __name__ == "__main__":

    from capabilities.base import (
        BaseCapability,
        CapabilityMetadata,
        CapabilityRequest,
        CapabilityResponse,
    )


    class DemoCapability(BaseCapability):

        metadata = CapabilityMetadata(
            name="Demo",
            version="1.0",
            description="Registry Test"
        )

        def execute(
            self,
            request: CapabilityRequest
        ) -> CapabilityResponse:

            return CapabilityResponse(
                success=True,
                message="Demo executed."
            )


    registry = CapabilityRegistry()

    registry.register(DemoCapability())

    print("===== CAPABILITY REGISTRY TEST =====")
    print()

    print("Count :", registry.count())
    print("Items :", registry.list_all())
    print("Exists:", registry.exists("Demo"))