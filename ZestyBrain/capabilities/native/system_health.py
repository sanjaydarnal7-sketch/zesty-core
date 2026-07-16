"""
Zesty OS
System Health Capability
Version: 1.0

Mission 52

Provides basic diagnostics about the local Zesty runtime.
"""

from __future__ import annotations

import os
import platform
import socket
from datetime import UTC, datetime

from capabilities.base import (
    BaseCapability,
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
)


class SystemHealthCapability(BaseCapability):
    """
    Returns diagnostic information about the
    current Zesty runtime.
    """

    metadata = CapabilityMetadata(
        name="system_health",
        version="1.0",
        description="Returns local system diagnostics.",
        author="Zesty OS",
        category="System",
    )

    def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResponse:

        health = {

            "zesty_version": "0.1",

            "platform": platform.system(),

            "platform_release": platform.release(),

            "python_version": platform.python_version(),

            "machine": platform.machine(),

            "hostname": socket.gethostname(),

            "working_directory": os.getcwd(),

            "current_time_utc": datetime.now(
                UTC
            ).isoformat(),

            "status": "Healthy",
        }

        return CapabilityResponse(
            success=True,
            message="System diagnostics completed.",
            data=health,
        )


# ----------------------------------------------------------------------
# Self Test
# ----------------------------------------------------------------------

if __name__ == "__main__":

    capability = SystemHealthCapability()

    request = CapabilityRequest(
        capability="system_health",
        payload={},
    )

    result = capability.execute(request)

    print("===== SYSTEM HEALTH TEST =====")
    print()

    print(result)