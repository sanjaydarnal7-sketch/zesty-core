from dataclasses import dataclass, field
from typing import List


@dataclass
class Fact:

    type: str
    value: str
    confidence: float
    source: str = "conversation"
    timestamp: str = ""


@dataclass
class LearningResult:

    identities: List[Fact] = field(default_factory=list)

    relationships: List[Fact] = field(default_factory=list)

    events: List[Fact] = field(default_factory=list)

    preferences: List[Fact] = field(default_factory=list)

    goals: List[Fact] = field(default_factory=list)

    ignored: bool = False


    def has_memory(self) -> bool:

        return any((
            self.identities,
            self.relationships,
            self.events,
            self.preferences,
            self.goals,
        ))

    def all_facts(self):

        return (
            self.identities
            + self.relationships
            + self.preferences
            + self.goals
            + self.events
        )
