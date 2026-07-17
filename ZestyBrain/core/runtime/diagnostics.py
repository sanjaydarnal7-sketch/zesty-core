"""
Zesty OS
Runtime Diagnostics

Mission 78

Provides diagnostic information about the runtime
environment.
"""

from __future__ import annotations

import platform
import sys
from datetime import datetime, timezone


class RuntimeDiagnostics:
    """
    Collects runtime diagnostic information.
    """

    def collect(self) -> dict:

        return {
            "python_version": sys.version.split()[0],
            "platform": platform.system(),
            "platform_release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "timestamp_utc": datetime.now(
                timezone.utc
            ).isoformat(),
        }


if __name__ == "__main__":

    diagnostics = RuntimeDiagnostics()

    print("===== ZESTY RUNTIME DIAGNOSTICS =====")

    for key, value in diagnostics.collect().items():
        print(f"{key}: {value}")