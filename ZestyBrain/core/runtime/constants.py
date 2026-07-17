"""
Zesty OS
Runtime Constants

Mission 80

Central runtime constants.
"""

from __future__ import annotations

# Runtime identity
RUNTIME_NAME = "Zesty OS Runtime"
RUNTIME_VERSION = "1.0.0"
RUNTIME_BUILD = "M80"

# Runtime states
STATE_STOPPED = "stopped"
STATE_STARTING = "starting"
STATE_RUNNING = "running"
STATE_STOPPING = "stopping"
STATE_FAILED = "failed"

# Health
HEALTHY = "healthy"
UNHEALTHY = "unhealthy"


if __name__ == "__main__":

    print("===== RUNTIME CONSTANTS =====")

    print("Runtime :", RUNTIME_NAME)
    print("Version :", RUNTIME_VERSION)
    print("Build   :", RUNTIME_BUILD)