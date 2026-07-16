"""
Zesty OS
Core Logging Engine
Version: 1.0

Mission 59

Central logging engine for the entire Zesty OS.

Every module should log through this engine.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


class LoggingEngine:
    """
    Central logger for Zesty OS.
    """

    def __init__(self):

        self.logs_path = (
            Path(__file__).parent.parent / "logs"
        )

        self.logs_path.mkdir(
            exist_ok=True
        )

        self.runtime_log = (
            self.logs_path / "runtime.log"
        )

        self.guardian_log = (
            self.logs_path / "guardian.log"
        )

        self.provider_log = (
            self.logs_path / "provider.log"
        )

        self.api_log = (
            self.logs_path / "api.log"
        )

    def _timestamp(self) -> str:

        return datetime.now(
            timezone.utc
        ).isoformat()

    def _write(
        self,
        file: Path,
        level: str,
        message: str,
    ) -> None:

        line = (
            f"[{self._timestamp()}] "
            f"[{level.upper()}] "
            f"{message}\n"
        )

        with open(
            file,
            "a",
            encoding="utf-8",
        ) as log:

            log.write(line)

        print(line, end="")

    # -------------------------

    def runtime(
        self,
        message: str,
        level: str = "INFO",
    ):

        self._write(
            self.runtime_log,
            level,
            message,
        )

    def guardian(
        self,
        message: str,
        level: str = "INFO",
    ):

        self._write(
            self.guardian_log,
            level,
            message,
        )

    def provider(
        self,
        message: str,
        level: str = "INFO",
    ):

        self._write(
            self.provider_log,
            level,
            message,
        )

    def api(
        self,
        message: str,
        level: str = "INFO",
    ):

        self._write(
            self.api_log,
            level,
            message,
        )


# -----------------------------------------------------
# Self Test
# -----------------------------------------------------

if __name__ == "__main__":

    logger = LoggingEngine()

    print("===== LOGGING ENGINE TEST =====")
    print()

    logger.runtime(
        "Runtime initialized."
    )

    logger.guardian(
        "Guardian policy approved capability."
    )

    logger.provider(
        "Provider selected: Grok."
    )

    logger.api(
        "API request completed."
    )

    print()
    print("Mission 59 Passed")