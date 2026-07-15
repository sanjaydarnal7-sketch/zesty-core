"""
Zesty OS
Personality Engine
Version: 1.0

Mission 42

Determines how Jessie should communicate
based on context, audience and conversation.
"""

from dataclasses import dataclass
from enum import Enum


class PersonalityMode(Enum):

    BUDDY = "buddy"

    EXECUTIVE = "executive"

    GUARDIAN = "guardian"

    TEACHER = "teacher"

    PRESENTER = "presenter"

    CHILD = "child"

    GUEST = "guest"


@dataclass
class PersonalityProfile:

    mode: PersonalityMode

    tone: str

    humor_level: int

    curiosity_level: int

    empathy_level: int

    response_length: str

    ask_follow_up: bool


class PersonalityEngine:

    def select(self, context: str):

        message = context.lower()

        # ------------------------
        # Competition / Presentation
        # ------------------------

        if any(word in message for word in [

            "competition",
            "judge",
            "stage",
            "presentation",
            "audience"

        ]):

            return PersonalityProfile(

                mode=PersonalityMode.PRESENTER,

                tone="confident",

                humor_level=3,

                curiosity_level=2,

                empathy_level=3,

                response_length="medium",

                ask_follow_up=False

            )

        # ------------------------
        # Business
        # ------------------------

        if any(word in message for word in [

            "client",
            "meeting",
            "proposal",
            "business"

        ]):

            return PersonalityProfile(

                mode=PersonalityMode.EXECUTIVE,

                tone="professional",

                humor_level=1,

                curiosity_level=3,

                empathy_level=3,

                response_length="medium",

                ask_follow_up=True

            )

        # ------------------------
        # Learning
        # ------------------------

        if any(word in message for word in [

            "learn",
            "teach",
            "research",
            "training"

        ]):

            return PersonalityProfile(

                mode=PersonalityMode.TEACHER,

                tone="curious",

                humor_level=2,

                curiosity_level=5,

                empathy_level=4,

                response_length="medium",

                ask_follow_up=True

            )

        # ------------------------
        # Kids
        # ------------------------

        if any(word in message for word in [

            "child",
            "kid",
            "kids"

        ]):

            return PersonalityProfile(

                mode=PersonalityMode.CHILD,

                tone="playful",

                humor_level=5,

                curiosity_level=5,

                empathy_level=5,

                response_length="short",

                ask_follow_up=True

            )

        # ------------------------
        # Guest
        # ------------------------

        if any(word in message for word in [

            "guest",
            "friend",
            "family"

        ]):

            return PersonalityProfile(

                mode=PersonalityMode.GUEST,

                tone="warm",

                humor_level=3,

                curiosity_level=4,

                empathy_level=5,

                response_length="medium",

                ask_follow_up=True

            )

        # ------------------------
        # Safety
        # ------------------------

        if any(word in message for word in [

            "danger",
            "risk",
            "emergency"

        ]):

            return PersonalityProfile(

                mode=PersonalityMode.GUARDIAN,

                tone="calm",

                humor_level=0,

                curiosity_level=2,

                empathy_level=5,

                response_length="short",

                ask_follow_up=False

            )

        # ------------------------
        # Default Buddy
        # ------------------------

        return PersonalityProfile(

            mode=PersonalityMode.BUDDY,

            tone="friendly",

            humor_level=3,

            curiosity_level=3,

            empathy_level=4,

            response_length="short",

            ask_follow_up=True

        )


if __name__ == "__main__":

    engine = PersonalityEngine()

    tests = [

        "Hello Jessie",

        "Business meeting tomorrow",

        "Teach me fermentation",

        "Cocktail competition presentation",

        "Guest is here",

        "Emergency"

    ]

    print("===== PERSONALITY ENGINE =====")

    print()

    for item in tests:

        print("Input :", item)

        print(engine.select(item))

        print("-" * 70)