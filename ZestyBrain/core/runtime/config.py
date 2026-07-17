"""
Zesty OS
Runtime Configuration Manager

Mission 84

Central configuration storage for runtime settings.
"""

from __future__ import annotations


class RuntimeConfig:
    """Stores runtime configuration values."""

    def __init__(self) -> None:
        self._config = {
            "app_name": "Zesty OS",
            "runtime_version": "1.0.0",
            "debug": False,
            "default_provider": "groq",
            "request_timeout": 30,
        }

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def set(self, key: str, value) -> None:
        self._config[key] = value

    def all(self) -> dict:
        return dict(self._config)


if __name__ == "__main__":

    print("===== ZESTY RUNTIME CONFIG =====")

    config = RuntimeConfig()

    print("App:", config.get("app_name"))
    print("Provider:", config.get("default_provider"))

    config.set("debug", True)

    print("Debug:", config.get("debug"))

    print("\nFull Configuration")

    for key, value in config.all().items():
        print(f"{key}: {value}")