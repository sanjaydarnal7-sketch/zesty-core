"""
Memory Pipeline

Coordinates learning, relationships,
conversation memory and structured fact memory.
"""

from __future__ import annotations

from ZestyBrain.learning.learning_engine import LearningEngine
from ZestyBrain.relationships.relationship_engine import RelationshipEngine

from ZestyBrain.memory.memory_engine import MemoryEngine
from ZestyBrain.memory.fact_memory import FactMemory


class MemoryPipeline:

    def __init__(
        self,
        memory: MemoryEngine,
        facts: FactMemory,
    ):

        self.learning = LearningEngine()

        self.relationships = RelationshipEngine()

        self.memory = memory

        self.facts = facts

    def process(self, text: str):

        result = self.learning.classify(text)

        if result.ignored:
            return result

        # Store conversation
        self.memory.remember(
            f"User: {text}"
        )

        # Learn from the conversation immediately
        self.memory.learn(text)

        # Identity facts
        for fact in result.identities:

            self.facts.remember_identity(
                fact.type,
                fact.value,
            )

        # Relationship facts
        for fact in result.relationships:

            self.relationships.remember_person(
                name=fact.value,
                relationship=fact.type,
            )

            self.facts.remember_relationship(
                fact.type,
                fact.value,
            )

        # Preferences
        for fact in result.preferences:

            self.facts.remember_preference(
                fact.type,
                fact.value,
            )

        # Goals
        for fact in result.goals:

            self.facts.remember_goal(
                fact.type,
                fact.value,
            )

        # Events
        for fact in result.events:

            self.facts.remember_event(
                fact.value,
            )

        return result
