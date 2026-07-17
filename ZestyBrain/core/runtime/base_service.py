"""
Zesty OS
Base Service Interface

Every runtime service must inherit from this class.
"""

from abc import ABC, abstractmethod
from enum import Enum


class ServiceState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    STOPPING = "stopping"


class BaseService(ABC):
    """
    Abstract base class for every Zesty runtime service.
    """

    def __init__(self, name: str):
        self.name = name
        self.state = ServiceState.STOPPED

    @abstractmethod
    def start(self):
        """Start the service."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the service."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the service is healthy."""
        pass

    def status(self):
        return {
            "service": self.name,
            "state": self.state.value,
        }