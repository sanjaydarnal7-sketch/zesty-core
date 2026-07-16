"""
Zesty OS
Time Capability
Version: 1.0

Mission 55

Provides current local and UTC date/time.
"""

from __future__ import annotations

from datetime import UTC, datetime

from capabilities.base import (
    BaseCapability,
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
)


class TimeCapability(BaseCapability):
    """
    Returns the current date and time.
    """

    metadata = CapabilityMetadata(
        name="time",
        version="1.0",
        description="Returns the current local and UTC time.",
        author="Zesty OS",
        category="System",
    )

    def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResponse:

        now_local = datetime.now()

        now_utc = datetime.now(UTC)

        data = {
            "local_time": now_local.isoformat(),
            "utc_time": now_utc.isoformat(),
            "local_date": now_local.strftime("%Y-%m-%d"),
            "local_clock": now_local.strftime("%H:%M:%S"),
            "timezone": str(now_local.astimezone().tzinfo),
        }

        return CapabilityResponse(
            success=True,
            message="Current time retrieved successfully.",
            data=data,
        )


# ----------------------------------------------------------------------
# Self Test
# ----------------------------------------------------------------------

if __name__ == "__main__":

    capability = TimeCapability()

    request = CapabilityRequest(
        capability="time",
        payload={},
    )

    result = capability.execute(request)

    print("===== TIME CAPABILITY TEST =====")
    print()

    print(result)