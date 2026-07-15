"""
Zesty OS
Shared Models
Version: 1.0

Mission 44

Provides common dataclasses shared across
all Zesty intelligence modules.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
import uuid


# ==========================================================
# Base Context
# ==========================================================

@dataclass(slots=True)
class UserContext:

    user_id: str = "default"

    user_name: str = "Sanjay"

    session_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )


# ==========================================================
# Conversation Context
# ==========================================================

@dataclass(slots=True)
class ConversationContext:

    message: str

    speaker: str = "user"

    channel: str = "chat"

    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )


# ==========================================================
# Engine Result
# ==========================================================

@dataclass(slots=True)
class EngineResult:

    success: bool

    engine: str

    data: Any

    message: str = ""


# ==========================================================
# Shared Metadata
# ==========================================================

@dataclass(slots=True)
class Metadata:

    created_by: str = "Jessie"

    version: str = "1.0"

    tags: list[str] = field(default_factory=list)


# ==========================================================
# Conversation Record
# ==========================================================

@dataclass(slots=True)
class ConversationRecord:

    id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

    context: ConversationContext = field(
        default_factory=lambda: ConversationContext(
            message=""
        )
    )

    metadata: Metadata = field(
        default_factory=Metadata
    )


# ==========================================================
# Demo
# ==========================================================

if __name__ == "__main__":

    context = ConversationContext(

        message="Hello Jessie"

    )

    result = EngineResult(

        success=True,

        engine="ConversationEngine",

        data=context,

        message="Shared model test successful."

    )

    print("===== SHARED MODELS =====")

    print()

    print(context)

    print()

    print(result)