"""
Persona Pipeline
Coordinates all persona-related engines before inference.
"""

from __future__ import annotations

from dataclasses import dataclass

from ZestyBrain.persona.persona_kernel import PersonaKernel


@dataclass
class PersonaContext:
    language: str
    behavior: object
    learning: object


class PersonaPipeline:

    def __init__(self):

        self.kernel = PersonaKernel()

    def process(
        self,
        text: str,
        mode: str = "buddy",
    ) -> PersonaContext:

        language = self.kernel.language(text)

        if mode == "buddy" and language == "hinglish":
            mode = "buddy"

        behavior = self.kernel.profile(mode)

        learning = self.kernel.classify(text)

        return PersonaContext(
            language=language,
            behavior=behavior,
            learning=learning,
        )
