from ZestyBrain.engines.memory.memory_engine import MemoryEngine
from ZestyBrain.engines.memory.models import MemoryRecord, MemoryType


def main() -> None:
    memory = MemoryEngine()

    record = MemoryRecord(
        id="001",
        type=MemoryType.WORKING,
        content="Hello Zesty"
    )

    memory.remember(record)

    recent = memory.recent()

    assert len(recent) == 1
    assert recent[0].content == "Hello Zesty"

    print("✅ Memory Engine OK")


if __name__ == "__main__":
    main()
