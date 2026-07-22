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

    "buddy": BehaviorProfile(
        name="buddy",
        tone="close friend, highly natural, energetic, emotionally intelligent",
        humor=True,
        asks_followup=True,
        empathy=True,
        concise=False,
    ),

    "friend": BehaviorProfile(
        name="friend",
        tone="best friend, natural, playful, emotionally aware",
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
        tone="buddy, modern, spoken, relaxed, human",
        humor=True,
        asks_followup=True,
        empathy=True,
        concise=False,
    ),
}


class BehaviorEngine:

    def profile(self, mode="buddy"):

        return PROFILES.get(mode, PROFILES["buddy"])
