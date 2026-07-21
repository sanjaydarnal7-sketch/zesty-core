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
