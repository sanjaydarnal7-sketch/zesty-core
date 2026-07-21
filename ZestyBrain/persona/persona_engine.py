"""
Zesty Persona Engine
"""

from __future__ import annotations

from ZestyBrain.persona.persona_loader import PersonaLoader
from ZestyBrain.persona.prompt_builder import PromptBuilder


class PersonaEngine:

    def __init__(self):

        self.loader = PersonaLoader()
        self.builder = PromptBuilder()

    @property
    def identity(self):

        return "Zesty"

    def build_system_prompt(
        self,
        user_prompt: str = "",
        memory_context: str = "",
    ) -> str:

        return self.builder.build(

            system_identity=self.loader.system_prompt(),

            memory_context=memory_context,

            user_message=user_prompt,
        )
