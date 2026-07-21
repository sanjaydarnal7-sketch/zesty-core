from dataclasses import dataclass, field
from typing import List


@dataclass
class Fact:

    type: str
    value: str
    confidence: float


@dataclass
class LearningResult:

    identities: List[Fact] = field(default_factory=list)

    relationships: List[Fact] = field(default_factory=list)

    events: List[Fact] = field(default_factory=list)

    preferences: List[Fact] = field(default_factory=list)

    goals: List[Fact] = field(default_factory=list)

    ignored: bool = False
