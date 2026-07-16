"""
Zesty OS
Guardian Policy Engine
Version: 1.0

Mission 56

Evaluates whether a capability is allowed to execute.
"""

from __future__ import annotations

from dataclasses import dataclass

from capabilities.base import BaseCapability


@dataclass(slots=True)
class GuardianDecision:
    """
    Result returned by the Guardian.
    """

    allowed: bool

    action: str

    reason: str


class GuardianPolicy:
    """
    Version 1 Policy Engine.

    Decision Rules

    low       -> allow

    medium    -> ask

    critical  -> deny
    """

    def evaluate(
        self,
        capability: BaseCapability,
    ) -> GuardianDecision:

        risk = capability.metadata.risk_level.lower()

        if risk == "low":

            return GuardianDecision(
                allowed=True,
                action="allow",
                reason="Low-risk capability.",
            )

        if risk == "medium":

            return GuardianDecision(
                allowed=False,
                action="ask",
                reason="User confirmation required.",
            )

        return GuardianDecision(
            allowed=False,
            action="deny",
            reason="Critical capability blocked.",
        )


# ----------------------------------------------------------------------
# Self Test
# ----------------------------------------------------------------------

if __name__ == "__main__":

    from capabilities.base import (
        CapabilityMetadata,
        CapabilityRequest,
        CapabilityResponse,
    )


    class DemoCapability(BaseCapability):

        metadata = CapabilityMetadata(
            name="demo",
            version="1.0",
            description="Guardian Test",
            risk_level="low",
        )

        def execute(
            self,
            request: CapabilityRequest,
        ) -> CapabilityResponse:

            return CapabilityResponse(
                success=True,
                message="OK",
            )


    guardian = GuardianPolicy()

    decision = guardian.evaluate(
        DemoCapability()
    )

    print("===== GUARDIAN POLICY TEST =====")
    print()

    print(decision)