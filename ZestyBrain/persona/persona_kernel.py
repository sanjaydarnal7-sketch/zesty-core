"""
Persona Kernel
Single entry point for all persona systems.
"""

from __future__ import annotations

from ZestyBrain.persona.identity import IDENTITY
from ZestyBrain.persona.user_profile import USER_PROFILE
from ZestyBrain.persona.language_engine import detect

from ZestyBrain.persona.behavior_engine import BehaviorEngine
from ZestyBrain.learning.learning_engine import LearningEngine
from ZestyBrain.relationships.relationship_engine import RelationshipEngine


class PersonaKernel:

    def __init__(self):

        self.identity = IDENTITY

        self.user = USER_PROFILE

        self.behavior = BehaviorEngine()

        self.learning = LearningEngine()

        self.relationships = RelationshipEngine()

    def language(self, text: str):

        return detect(text)

    def profile(self, mode="casual"):

        return self.behavior.profile(mode)

    def classify(self, text: str):

        return self.learning.classify(text)

    def remember_person(
        self,
        name,
        relationship,
        organization="",
        importance=5,
    ):

        return self.relationships.remember_person(
            name=name,
            relationship=relationship,
            organization=organization,
            importance=importance,
        )

    def person(self, name):

        return self.relationships.get(name)
