"""
Zesty OS
Runtime Version

Mission 79

Provides version and build information
for the Zesty Runtime.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeVersion:
    """
    Immutable runtime version information.
    """

    name: str = "Zesty OS Runtime"
    version: str = "1.0.0"
    build: str = "M79"
    codename: str = "Foundation"

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "version": self.version,
            "build": self.build,
            "codename": self.codename,
        }


if __name__ == "__main__":

    runtime = RuntimeVersion()

    print("===== ZESTY RUNTIME VERSION =====")

    for key, value in runtime.as_dict().items():
        print(f"{key}: {value}")