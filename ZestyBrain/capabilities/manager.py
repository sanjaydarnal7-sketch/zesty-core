"""
Zesty OS
Capability Manager
Version: 1.0

Mission 51

Executes registered capabilities in a standardized manner.
"""

from __future__ import annotations

from time import perf_counter

from capabilities.base import (
    BaseCapability,
    CapabilityRequest,
)
from capabilities.result import CapabilityResult


class CapabilityManager:
    """
    Executes capabilities and converts every execution
    into a standard CapabilityResult.
    """

    def execute(
        self,
        capability: BaseCapability,
        request: CapabilityRequest,
    ) -> CapabilityResult:

        start = perf_counter()

        try:

            response = capability.execute(request)

            elapsed = (perf_counter() - start) * 1000

            return CapabilityResult(
                success=response.success,
                message=response.message,
                data=response.data,
                execution_time_ms=elapsed,
                capability_name=capability.metadata.name,
                provider="Local",
            )

        except Exception as error:

            elapsed = (perf_counter() - start) * 1000

            return CapabilityResult(
                success=False,
                message="Capability execution failed.",
                execution_time_ms=elapsed,
                capability_name=getattr(
                    capability.metadata,
                    "name",
                    "Unknown",
                ),
                provider="Local",
                errors=[str(error)],
            )


# ----------------------------------------------------------------------
# Self Test
# ----------------------------------------------------------------------

if __name__ == "__main__":

    from capabilities.base import (
        CapabilityMetadata,
        CapabilityResponse,
    )


    class DemoCapability(BaseCapability):

        metadata = CapabilityMetadata(
            name="Demo",
            version="1.0",
            description="Manager Self Test",
        )

        def execute(
            self,
            request: CapabilityRequest,
        ) -> CapabilityResponse:

            return CapabilityResponse(
                success=True,
                message="Hello from Demo Capability",
                data=request.payload,
            )


    manager = CapabilityManager()

    request = CapabilityRequest(
        capability="demo",
        payload={
            "message": "Hello Jessie"
        },
    )

    result = manager.execute(
        DemoCapability(),
        request,
    )

    print("===== CAPABILITY MANAGER TEST =====")
    print()

    print(result)