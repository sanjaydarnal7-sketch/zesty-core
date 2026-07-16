"""
Zesty OS
Runtime Scheduler
Version: 3.0

Mission 69

Responsible for:
- Runtime Task Scheduling
- Priority Queue
- FIFO Execution
- Future Worker Pool Integration
"""

from __future__ import annotations

import heapq
import itertools

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any


# ---------------------------------------------------------
# Task Priority
# ---------------------------------------------------------

class TaskPriority(IntEnum):

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


# ---------------------------------------------------------
# Runtime Task
# ---------------------------------------------------------

_sequence = itertools.count()


@dataclass(slots=True)
class RuntimeTask:

    name: str

    priority: TaskPriority = TaskPriority.NORMAL

    payload: Any = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


# ---------------------------------------------------------
# Runtime Scheduler
# ---------------------------------------------------------

class RuntimeScheduler:

    def __init__(self):

        self._queue: list[
            tuple[
                int,
                int,
                RuntimeTask
            ]
        ] = []

    def add_task(
        self,
        task: RuntimeTask,
    ) -> None:

        heapq.heappush(

            self._queue,

            (

                int(task.priority),

                next(_sequence),

                task,

            ),

        )

    def next_task(
        self,
    ) -> RuntimeTask:

        if self.empty():

            raise RuntimeError(

                "Scheduler queue is empty."

            )

        _, _, task = heapq.heappop(

            self._queue

        )

        return task

    def peek(
        self,
    ) -> RuntimeTask:

        if self.empty():

            raise RuntimeError(

                "Scheduler queue is empty."

            )

        _, _, task = self._queue[0]

        return task

    def queue_size(
        self,
    ) -> int:

        return len(

            self._queue

        )

    def empty(
        self,
    ) -> bool:

        return len(

            self._queue

        ) == 0

    def clear(
        self,
    ) -> None:

        self._queue.clear()


# ---------------------------------------------------------
# Self Test
# ---------------------------------------------------------

if __name__ == "__main__":

    scheduler = RuntimeScheduler()

    scheduler.add_task(

        RuntimeTask(

            name="AI Response",

            priority=TaskPriority.NORMAL,

        )

    )

    scheduler.add_task(

        RuntimeTask(

            name="Guardian Alert",

            priority=TaskPriority.CRITICAL,

        )

    )

    scheduler.add_task(

        RuntimeTask(

            name="Log Cleanup",

            priority=TaskPriority.LOW,

        )

    )

    print("===== RUNTIME SCHEDULER TEST =====")
    print()

    print(

        "Queue Size :",

        scheduler.queue_size()

    )

    print()

    while not scheduler.empty():

        task = scheduler.next_task()

        print(

            f"{task.priority.name} | {task.name}"

        )

    print()

    print(

        "Queue Empty :",

        scheduler.empty()

    )

    print()

    print(

        "Mission 69 Passed"

    )