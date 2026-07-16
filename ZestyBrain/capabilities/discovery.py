"""
Zesty OS
Capability Discovery
Version: 1.0

Mission 54

Automatically discovers and registers native capabilities.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

from capabilities.base import BaseCapability
from capabilities.registry import CapabilityRegistry


class CapabilityDiscovery:
    """
    Automatically discovers native capabilities.

    Future:

        Native
        Plugins
        MCP
        Remote
    """

    def __init__(self, registry: CapabilityRegistry):

        self.registry = registry

    def discover_native(self) -> int:

        count = 0

        import capabilities.native as native_package

        for _, module_name, _ in pkgutil.iter_modules(
            native_package.__path__
        ):

            module = importlib.import_module(
                f"capabilities.native.{module_name}"
            )

            for _, obj in inspect.getmembers(
                module,
                inspect.isclass,
            ):

                if (
                    issubclass(obj, BaseCapability)
                    and obj is not BaseCapability
                ):

                    capability = obj()

                    if not self.registry.exists(
                        capability.metadata.name
                    ):

                        self.registry.register(
                            capability
                        )

                        count += 1

        return count


# ----------------------------------------------------------------------
# Self Test
# ----------------------------------------------------------------------

if __name__ == "__main__":

    registry = CapabilityRegistry()

    discovery = CapabilityDiscovery(
        registry
    )

    total = discovery.discover_native()

    print("===== CAPABILITY DISCOVERY TEST =====")
    print()

    print("Discovered :", total)

    print("Registry   :", registry.list_all())