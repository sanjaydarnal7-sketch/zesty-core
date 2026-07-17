"""Canonical runtime coordinator for Zesty OS.

The runtime manager owns process-level runtime dependencies and coordinates
their lifecycle.  It deliberately does not execute providers, access memory,
or depend on a user-interface framework.
"""

from __future__ import annotations

from typing import Any

from config.config_manager import ConfigManager
from config.secret_manager import SecretManager
from core.runtime.base_service import BaseService
from core.runtime.context import RuntimeContext
from core.runtime.health_monitor import RuntimeHealthMonitor
from core.runtime.lifecycle import RuntimePhase
from core.runtime.service_manager import ServiceManager
from providers.bootstrap import ProviderBootstrap
from providers.registry import Provider, ProviderRegistry


class RuntimeManager:
    """Coordinate Zesty OS runtime initialization and service lifecycle.

    Provider registration retains the existing behavior of the legacy runtime
    manager.  ``execute`` intentionally returns the same metadata-only result
    and does not invoke a provider.
    """

    def __init__(self, context: RuntimeContext | None = None) -> None:
        self.context = context or RuntimeContext()
        self.lifecycle = self.context.lifecycle
        self.state = self.context.state
        self.runtime_config = self.context.config
        self.events = self.context.events

        self.service_manager = ServiceManager()
        self.health_monitor = RuntimeHealthMonitor()

        # Preserve the existing configuration, secret, and provider setup.
        self.config = ConfigManager()
        self.secrets = SecretManager()
        self.registry = ProviderRegistry()
        ProviderBootstrap().load(self.registry)

        self._initialized = False

    @property
    def initialized(self) -> bool:
        """Return whether the runtime has completed initialization."""
        return self._initialized

    def initialize(self) -> None:
        """Initialize the runtime foundations and start registered services."""
        phase = self.lifecycle.get_phase()
        if phase is RuntimePhase.RUNNING:
            self._initialized = True
            return
        if phase is RuntimePhase.STOPPING:
            raise RuntimeError("Runtime cannot initialize while stopping.")

        self.lifecycle.set_phase(RuntimePhase.STARTING)
        self.state.set("runtime_status", "starting")

        try:
            self.service_manager.start_all()
        except Exception:
            self.state.set("runtime_status", "failed")
            self.lifecycle.set_phase(RuntimePhase.FAILED)
            raise

        self.state.set("runtime_status", "running")
        self.state.set("runtime_manager_initialized", True)
        self.lifecycle.set_phase(RuntimePhase.RUNNING)
        self._initialized = True

    def shutdown(self) -> None:
        """Stop registered services and transition the runtime to stopped."""
        if self.lifecycle.get_phase() is RuntimePhase.STOPPED:
            self._initialized = False
            return

        self.lifecycle.set_phase(RuntimePhase.STOPPING)
        self.state.set("runtime_status", "stopping")

        self.service_manager.stop_all()

        self.state.set("runtime_status", "stopped")
        self.state.remove("runtime_manager_initialized")
        self.lifecycle.set_phase(RuntimePhase.STOPPED)
        self._initialized = False

    def register_service(self, service: BaseService) -> None:
        """Register a lifecycle-managed service with runtime monitoring."""
        self.service_manager.register(service)
        self.health_monitor.register(service.name, service)

    def get_active_provider(self) -> Provider | None:
        """Return the configured provider descriptor without invoking it."""
        provider_name = self.config.get("active_provider", "grok")
        return self.registry.get(provider_name)

    def execute(self, prompt: str) -> dict[str, Any]:
        """Return the existing metadata-only execution response.

        This method preserves the pre-migration provider behavior.  Provider
        execution belongs to a later integration phase.
        """
        self.initialize()
        provider = self.get_active_provider()
        if provider is None:
            raise RuntimeError("Configured provider is not registered.")

        return {
            "provider": provider.name,
            "prompt": prompt,
            "status": "ready",
            "message": "Runtime Manager initialized.",
        }

    def health_report(self) -> dict[str, Any]:
        """Return runtime lifecycle and registered-service health details."""
        return {
            "phase": self.lifecycle.get_phase().value,
            "initialized": self.initialized,
            "services": self.health_monitor.report(),
        }
