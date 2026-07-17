"""
Zesty OS
Runtime Environment

Mission 82

Provides runtime environment information.
"""

from __future__ import annotations

import os
import platform


class RuntimeEnvironment:
    """Runtime environment information."""

    @staticmethod
    def info() -> dict[str, str]:
        return {
            "os": platform.system(),
            "release": platform.release(),
            "python": platform.python_version(),
            "architecture": platform.machine(),
            "cwd": os.getcwd(),
        }


if __name__ == "__main__":

    print("===== ZESTY RUNTIME ENVIRONMENT =====")

    for key, value in RuntimeEnvironment.info().items():
        print(f"{key}: {value}")