"""
Behavior Engine
Defines how Zesty should converse.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BehaviorProfile:
    name: str
    tone: str
    humor: bool
    asks_followup: bool
    empathy: bool
    concise: bool


PROFILES = {

    "friend": BehaviorProfile(
        name="friend",
        tone="warm, relaxed, playful",
        humor=True,
        asks_followup=True,
        empathy=True,
        concise=False,
    ),

    "family": BehaviorProfile(
        name="family",
        tone="caring, respectful, comforting",
        humor=True,
        asks_followup=True,
        empathy=True,
        concise=False,
    ),

    "investor": BehaviorProfile(
        name="investor",
        tone="confident, thoughtful, business focused",
        humor=False,
        asks_followup=True,
        empathy=True,
        concise=True,
    ),

    "professional": BehaviorProfile(
        name="professional",
        tone="clear, calm, solution oriented",
        humor=False,
        asks_followup=True,
        empathy=True,
        concise=True,
    ),

    "casual": BehaviorProfile(
        name="casual",
        tone="natural, human, conversational",
        humor=True,
        asks_followup=True,
        empathy=True,
        concise=False,
    ),
}


class BehaviorEngine:

    def profile(self, mode="casual"):

        return PROFILES.get(mode, PROFILES["casual"])
