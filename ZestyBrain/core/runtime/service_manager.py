"""
Zesty OS
Service Manager
"""

from core.runtime.service_registry import ServiceRegistry
from core.runtime.base_service import ServiceState


class ServiceManager:
    """
    Controls the lifecycle of all runtime services.
    """

    def __init__(self):
        self.registry = ServiceRegistry()

    def register(self, service):
        self.registry.register(service)

    def start_all(self):
        """
        Start every registered service.
        """
        for service in self.registry.all():
            if service.state == ServiceState.STOPPED:
                service.state = ServiceState.STARTING

                try:
                    service.start()
                    service.state = ServiceState.RUNNING

                except Exception as e:
                    service.state = ServiceState.FAILED
                    print(f"[FAILED] {service.name}: {e}")

    def stop_all(self):
        """
        Stop every running service.
        """
        for service in self.registry.all():
            if service.state == ServiceState.RUNNING:
                service.state = ServiceState.STOPPING

                try:
                    service.stop()
                    service.state = ServiceState.STOPPED

                except Exception as e:
                    service.state = ServiceState.FAILED
                    print(f"[FAILED] {service.name}: {e}")

    def health_report(self):
        """
        Return health information for every service.
        """
        report = {}

        for service in self.registry.all():
            report[service.name] = {
                "state": service.state.value,
                "healthy": service.health_check()
            }

        return report