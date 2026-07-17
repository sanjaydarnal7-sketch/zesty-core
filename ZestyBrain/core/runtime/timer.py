"""
Zesty OS
Runtime Timer

Mission 83

Provides simple runtime timing utilities.
"""

from __future__ import annotations

import time


class RuntimeTimer:
    """Simple runtime performance timer."""

    def __init__(self) -> None:
        self._start = None

    def start(self) -> None:
        self._start = time.perf_counter()

    def stop(self) -> float:
        if self._start is None:
            raise RuntimeError("Timer has not been started.")

        elapsed = time.perf_counter() - self._start
        self._start = None
        return elapsed


if __name__ == "__main__":

    print("===== ZESTY RUNTIME TIMER =====")

    timer = RuntimeTimer()

    timer.start()

    time.sleep(1)

    elapsed = timer.stop()

    print(f"Elapsed Time: {elapsed:.3f} seconds")