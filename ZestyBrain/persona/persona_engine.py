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

        return (
            "Zesty — Sanjay's AI Buddy. "
            "Speaks naturally like a close friend. "
            "Maintains long-term memory, conversation continuity, "
            "and switches naturally between Hindi, English and Hinglish."
        )

    def build_system_prompt(
        self,
        user_prompt: str = "",
        memory_context: str = "",
        language: str = "",
        behavior=None,
        learning=None,
    ) -> str:

        return self.builder.build(

            system_identity=(
                self.loader.system_prompt()
                + "\n\n"
                + self.identity
            ),

            memory_context=memory_context,

            user_message=user_prompt,

            language=language,

            behavior=behavior,

            learning=learning,
        )
