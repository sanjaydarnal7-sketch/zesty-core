"""
Zesty OS
Service Registry
"""

from typing import Dict

from core.runtime.base_service import BaseService


class ServiceRegistry:
    """
    Stores all runtime services.
    """

    def __init__(self):
        self._services: Dict[str, BaseService] = {}

    def register(self, service: BaseService):
        """
        Register a runtime service.
        """
        self._services[service.name] = service

    def unregister(self, name: str):
        """
        Remove a service.
        """
        self._services.pop(name, None)

    def get(self, name: str):
        """
        Get a service by name.
        """
        return self._services.get(name)

    def all(self):
        """
        Return all registered services.
        """
        return list(self._services.values())

    def exists(self, name: str):
        return name in self._services