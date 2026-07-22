from __future__ import annotations

from dataclasses import asdict, is_dataclass

from .conversation_director import ConversationDirector


class PromptBuilder:

    def __init__(self):
        self.director = ConversationDirector()

    def _format_learning(self, learning):

        if learning is None:
            return "No learned information."

        if is_dataclass(learning):
            learning = asdict(learning)

        if not isinstance(learning, dict):
            return str(learning)

        lines = []

        for key, value in learning.items():

            if key == "ignored":
                continue

            title = key.replace("_", " ").title()

            lines.append(f"{title}:")

            if value:
                if isinstance(value, list):
                    for item in value:
                        lines.append(f"- {item}")
                else:
                    lines.append(f"- {value}")
            else:
                lines.append("- None")

            lines.append("")

        return "\n".join(lines).strip()

    def build(
        self,
        *,
        system_identity: str,
        memory_context: str = "",
        user_message: str = "",
        language: str = "",
        behavior=None,
        learning=None,
    ) -> str:

        director = self.director.build()


        conversation_rules = [
            "",
            "==============================",
            "CONVERSATION RULES",
            "==============================",
            "- Talk like a close buddy, not a chatbot.",
            "- Continue previous conversations naturally.",
            "- Do not re-introduce yourself.",
            "- Do not say you are an AI.",
            "- Switch naturally between Hindi, English and Hinglish.",
            "- Take initiative when appropriate.",
            "- Avoid repetitive greetings.",
        ]

        sections = [
            "==============================",
            "SYSTEM IDENTITY",
            "==============================",
            system_identity.strip(),

            "",
            "==============================",
            "CONVERSATION DIRECTOR",
            "==============================",
        ]

        for key, value in director.items():
            sections.append(f"{key}: {value}")


        sections.extend(conversation_rules)

        if language:
            sections.extend([
                "",
                "==============================",
                "LANGUAGE",
                "==============================",
                f"Preferred response language: {language}",
            ])

        if behavior:

            if is_dataclass(behavior):
                behavior = asdict(behavior)

            sections.extend([
                "",
                "==============================",
                "BEHAVIOR PROFILE",
                "==============================",
            ])

            for key, value in behavior.items():
                sections.append(f"{key}: {value}")

        if learning:

            sections.extend([
                "",
                "==============================",
                "LEARNING CONTEXT",
                "==============================",
                self._format_learning(learning),
            ])

        if memory_context.strip():

            sections.extend([
                "",
                "==============================",
                "LONG-TERM & RECENT MEMORY",
                "==============================",
                "Use this memory as established facts and previous conversation.",
                "Never contradict it unless the user explicitly corrects it.",
                "",
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
