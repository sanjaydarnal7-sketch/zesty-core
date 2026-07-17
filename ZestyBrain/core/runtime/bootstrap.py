"""
Zesty OS
Runtime Bootstrap

Mission 77

Initializes the Zesty Runtime.
"""

from core.runtime.runtime_kernel import RuntimeKernel
from core.runtime.service_manager import ServiceManager


class RuntimeBootstrap:
    """
    Boots the Zesty runtime.
    """

    def __init__(self):
        self.kernel = RuntimeKernel()
        self.services = ServiceManager()

    def boot(self):
        self.kernel.start()
        self.services.start_all()

    def shutdown(self):
        self.services.stop_all()
        self.kernel.stop()


if __name__ == "__main__":
    runtime = RuntimeBootstrap()

    print("=== BOOTING ZESTY ===")
    runtime.boot()

    print("Runtime Running:", runtime.kernel.running())

    print("=== SHUTTING DOWN ===")
    runtime.shutdown()

    print("Runtime Running:", runtime.kernel.running())