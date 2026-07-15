"""
Zesty OS
Memory Engine
Version: 2.0

Mission 35

Long-term memory storage engine.

Responsibilities:
- Store structured memories
- Assign unique IDs
- Store timestamps
- Prepare memories for future search
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid4
from typing import List


@dataclass
class MemoryItem:

    id: str

    category: str

    title: str

    content: str

    tags: List[str] = field(default_factory=list)

    source: str = "conversation"

    created_at: str = ""


class MemoryEngine:

    def __init__(self):

        self.memories: List[MemoryItem] = []

    def store(
        self,
        category: str,
        title: str,
        content: str,
        tags: List[str] | None = None,
        source: str = "conversation"
    ) -> MemoryItem:

        if tags is None:
            tags = []

        memory = MemoryItem(

            id=str(uuid4()),

            category=category,

            title=title,

            content=content,

            tags=tags,

            source=source,

            created_at=datetime.now(UTC).isoformat()

        )

        self.memories.append(memory)

        return memory

    def get(self, memory_id: str):

        for memory in self.memories:

            if memory.id == memory_id:

                return memory

        return None

    def list_all(self):

        return self.memories

    def count(self):

        return len(self.memories)

    def clear(self):

        self.memories.clear()


if __name__ == "__main__":

    engine = MemoryEngine()

    engine.store(

        category="recipe",

        title="Negroni",

        content="Classic gin cocktail.",

        tags=[
            "gin",
            "campari",
            "classic"
        ]

    )

    engine.store(

        category="business",

        title="Sector Gin",

        content="Future collaboration project.",

        tags=[
            "brand",
            "gin",
            "collaboration"
        ]

    )

    print("===== MEMORY ENGINE =====")

    print()

    print("Total Memories:", engine.count())

    print()

    for memory in engine.list_all():

        print(memory)

        print("-" * 60)