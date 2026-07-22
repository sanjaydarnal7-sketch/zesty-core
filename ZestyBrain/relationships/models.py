"""
Relationship Models
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Person:

    name: str

    relationship: str

    importance: int = 5

    organization: str = ""

    notes: List[str] = field(default_factory=list)

    preferences: List[str] = field(default_factory=list)

    aliases: List[str] = field(default_factory=list)

    last_seen: str = ""


    def summary(self):

        return {
            "name": self.name,
            "relationship": self.relationship,
            "organization": self.organization,
            "importance": self.importance,
            "aliases": self.aliases,
            "notes": self.notes,
            "preferences": self.preferences,
            "last_seen": self.last_seen,
        }

    def add_alias(self, alias):

        if alias and alias not in self.aliases:
            self.aliases.append(alias)
