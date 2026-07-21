"""
Zesty Prompt Builder
"""

from __future__ import annotations


class PromptBuilder:

    def build(
        self,
        *,
        system_identity: str,
        memory_context: str = "",
        user_message: str = "",
    ) -> str:

        sections = [

            "==============================",
            "SYSTEM IDENTITY",
            "==============================",
            system_identity.strip(),
        ]

        if memory_context.strip():

            sections.extend([

                "",
                "==============================",
                "RECENT MEMORY",
                "==============================",
                memory_context.strip(),
            ])

        if user_message.strip():

            sections.extend([

                "",
                "==============================",
                "CURRENT USER MESSAGE",
                "==============================",
                user_message.strip(),
            ])

        return "\n".join(sections)
