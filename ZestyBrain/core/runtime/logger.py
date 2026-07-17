"""
Zesty OS
Runtime Logger

Mission 81

Lightweight runtime logger for console output.
"""

from __future__ import annotations

from datetime import datetime


class RuntimeLogger:
    """Simple runtime logger."""

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def info(cls, message: str) -> None:
        print(f"[{cls._timestamp()}] [INFO] {message}")

    @classmethod
    def warning(cls, message: str) -> None:
        print(f"[{cls._timestamp()}] [WARNING] {message}")

    @classmethod
    def error(cls, message: str) -> None:
        print(f"[{cls._timestamp()}] [ERROR] {message}")


if __name__ == "__main__":
    print("===== ZESTY RUNTIME LOGGER =====")

    RuntimeLogger.info("Runtime initialized.")
    RuntimeLogger.warning("Low memory simulation.")
    RuntimeLogger.error("Example runtime error.")