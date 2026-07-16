"""
Zesty OS
Capability Result
Version: 2.1

Mission 49

Enterprise execution result shared by all capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class CapabilityResult:
    """
    Standard execution result returned by every Jessie capability.

    This object is shared across:
    - Native Capabilities
    - MCP Capabilities
    - Plugin Capabilities
    - Guardian Core
    - AI Control Center
    - Logging System
    - Analytics Engine
    """

    success: bool

    message: str

    data: Any | None = None

    execution_time_ms: float = 0.0

    warnings: list[str] = field(default_factory=list)

    errors: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    capability_name: str = ""

    provider: str = ""

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def has_errors(self) -> bool:
        """Return True if execution contains errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Return True if execution contains warnings."""
        return len(self.warnings) > 0

    def add_warning(self, warning: str) -> None:
        """Append a warning message."""
        self.warnings.append(warning)

    def add_error(self, error: str) -> None:
        """Append an error message."""
        self.errors.append(error)

    def to_dict(self) -> dict[str, Any]:
        """Convert the result into a serializable dictionary."""

        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "execution_time_ms": self.execution_time_ms,
            "warnings": self.warnings,
            "errors": self.errors,
            "metadata": self.metadata,
            "capability_name": self.capability_name,
            "provider": self.provider,
            "timestamp": self.timestamp.isoformat(),
        }


if __name__ == "__main__":

    result = CapabilityResult(
        success=True,
        message="Capability executed successfully.",
        capability_name="Demo",
        provider="Local",
        execution_time_ms=15.8,
        data={
            "status": "completed"
        },
    )

    print("===== CAPABILITY RESULT TEST =====")
    print()

    print(result)

    print()

    print("Dictionary Export")

    print(result.to_dict())