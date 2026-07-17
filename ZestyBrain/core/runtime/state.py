"""
Zesty OS
Runtime State Manager

Mission 87

Central runtime state storage.
"""

from __future__ import annotations


class RuntimeState:
    """Stores runtime state values."""

    def __init__(self) -> None:
        self._state = {}

    def set(self, key: str, value) -> None:
        """Store a runtime state value."""
        self._state[key] = value

    def get(self, key: str, default=None):
        """Retrieve a runtime state value."""
        return self._state.get(key, default)

    def remove(self, key: str) -> None:
        """Remove a runtime state value if present."""
        self._state.pop(key, None)

    def all(self) -> dict:
        """Return a copy of the current runtime state."""
        return dict(self._state)


if __name__ == "__main__":

    print("===== ZESTY RUNTIME STATE =====")

    state = RuntimeState()

    state.set("runtime_status", "running")
    state.set("active_provider", "groq")
    state.set("voice_enabled", True)

    print("Status:", state.get("runtime_status"))
    print("Provider:", state.get("active_provider"))
    print("Voice:", state.get("voice_enabled"))

    print("\nCurrent Runtime State")

    for key, value in state.all().items():
        print(f"{key}: {value}")