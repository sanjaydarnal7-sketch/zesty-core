"""
Zesty OS
Guardian Controller
Version: 1.0

Mission 57

Coordinates Guardian policy checks before
executing a capability.
"""

from __future__ import annotations

from capabilities.base import (
    BaseCapability,
    CapabilityRequest,
)
from capabilities.manager import CapabilityManager
from capabilities.result import CapabilityResult
from guardian.policy import GuardianPolicy


class GuardianController:
    """
    Executes capabilities only after
    Guardian approval.
    """

    def __init__(self):

        self.guardian = GuardianPolicy()

        self.manager = CapabilityManager()

    def execute(
        self,
        capability: BaseCapability,
        request: CapabilityRequest,
    ) -> CapabilityResult:

        decision = self.guardian.evaluate(
            capability
        )

        if decision.action == "deny":

            return CapabilityResult(
                success=False,
                message="Blocked by Guardian.",
                capability_name=capability.metadata.name,
                provider="Guardian",
                errors=[decision.reason],
            )

        if decision.action == "ask":

            return CapabilityResult(
                success=False,
                message="User confirmation required.",
                capability_name=capability.metadata.name,
                provider="Guardian",
                warnings=[decision.reason],
            )

        return self.manager.execute(
            capability,
            request,
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
            name="demo",
            version="1.0",
            description="Guardian Controller Test",
            risk_level="low",
        )

        def execute(
            self,
            request: CapabilityRequest,
        ) -> CapabilityResponse:

            return CapabilityResponse(
                success=True,
                message="Execution Successful",
                data={"status": "ok"},
            )


    controller = GuardianController()

    request = CapabilityRequest(
        capability="demo",
        payload={},
    )

    result = controller.execute(
        DemoCapability(),
        request,
    )

    print("===== GUARDIAN CONTROLLER TEST =====")
    print()
    print(result)