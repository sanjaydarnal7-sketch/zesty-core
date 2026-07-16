"""
Zesty OS
Capability Integration Test
Version: 1.0

Mission 53

End-to-End integration test for the Capability Engine.
"""

from capabilities.registry import CapabilityRegistry
from capabilities.router import CapabilityRouter
from capabilities.manager import CapabilityManager
from capabilities.base import CapabilityRequest
from capabilities.native.system_health import SystemHealthCapability


def run_test():

    print("===== CAPABILITY INTEGRATION TEST =====")
    print()

    # ------------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------------

    registry = CapabilityRegistry()

    capability = SystemHealthCapability()

    registry.register(capability)

    print("[PASS] Capability Registered")

    # ------------------------------------------------------------------
    # Router
    # ------------------------------------------------------------------

    router = CapabilityRouter(registry)

    selected = router.route("system_health")

    if selected is None:
        raise RuntimeError("Router failed.")

    print("[PASS] Router Located Capability")

    # ------------------------------------------------------------------
    # Manager
    # ------------------------------------------------------------------

    manager = CapabilityManager()

    request = CapabilityRequest(
        capability="system_health",
        payload={}
    )

    result = manager.execute(
        selected,
        request
    )

    if not result.success:
        raise RuntimeError(result.message)

    print("[PASS] Capability Executed")

    print()

    print("===== RESULT =====")
    print(result)

    print()

    print("MISSION 53 PASSED")


if __name__ == "__main__":

    run_test()