"""
Zesty OS
Capability Router
Version: 3.0

Mission 50

Routes capability requests to the correct registered capability.
"""

from __future__ import annotations

from capabilities.base import (
    BaseCapability,
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
)
from capabilities.registry import CapabilityRegistry


class CapabilityRouter:
    """
    Responsible for locating capabilities.

    Future Routing Order

        Native
           ↓
         MCP
           ↓
       Plugins
    """

    def __init__(self, registry: CapabilityRegistry):

        self.registry = registry

    def route(
        self,
        capability_name: str,
    ) -> BaseCapability | None:

        return self.registry.get(capability_name)

    def exists(
        self,
        capability_name: str,
    ) -> bool:

        return self.registry.exists(capability_name)


# ----------------------------------------------------------------------
# Self Test
# ----------------------------------------------------------------------

if __name__ == "__main__":

    class DemoCapability(BaseCapability):

        metadata = CapabilityMetadata(
            name="Demo",
            version="1.0",
            description="Router Self Test",
            author="Zesty",
            category="Testing",
        )

        def execute(
            self,
            request: CapabilityRequest,
        ) -> CapabilityResponse:

            return CapabilityResponse(
                success=True,
                message="Demo Executed",
            )


    registry = CapabilityRegistry()

    registry.register(DemoCapability())

    router = CapabilityRouter(registry)

    print("===== CAPABILITY ROUTER TEST =====")
    print()

    print("Exists :", router.exists("Demo"))

    capability = router.route("Demo")

    print("Found  :", capability is not None)

    print("Missing:", router.route("Missing"))