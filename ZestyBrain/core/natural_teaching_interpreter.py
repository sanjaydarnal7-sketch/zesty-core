"""
Zesty OS
Natural Teaching Interpreter
Version: 1.0

Mission 41

Interprets natural language instructions and
decides how Zesty should learn from them.
"""

from dataclasses import dataclass


@dataclass
class TeachingDecision:

    intent: str

    workspace: str

    priority: str

    action: str

    reason: str


class NaturalTeachingInterpreter:

    def interpret(self, text: str):

        message = text.lower()

        # -----------------------------
        # Competition Training
        # -----------------------------

        if any(keyword in message for keyword in [

            "competition",
            "cocktail",
            "judge",
            "presentation",
            "bar mysterio",
            "stage"

        ]):

            return TeachingDecision(

                intent="training",

                workspace="competition",

                priority="high",

                action="store_training_note",

                reason="Competition related knowledge."

            )

        # -----------------------------
        # Business
        # -----------------------------

        if any(keyword in message for keyword in [

            "client",
            "proposal",
            "meeting",
            "business",
            "partner"

        ]):

            return TeachingDecision(

                intent="training",

                workspace="business",

                priority="high",

                action="store_training_note",

                reason="Business preparation."

            )

        # -----------------------------
        # Permanent Memory
        # -----------------------------

        if any(keyword in message for keyword in [

            "always remember",

            "remember forever",

            "important memory",

            "permanent"

        ]):

            return TeachingDecision(

                intent="memory",

                workspace="long_term",

                priority="critical",

                action="save_memory",

                reason="User requested permanent memory."

            )

        # -----------------------------
        # Ignore
        # -----------------------------

        if any(keyword in message for keyword in [

            "don't remember",

            "do not remember",

            "ignore this",

            "temporary"

        ]):

            return TeachingDecision(

                intent="temporary",

                workspace="none",

                priority="low",

                action="ignore",

                reason="Temporary discussion."

            )

        # -----------------------------
        # Default
        # -----------------------------

        return TeachingDecision(

            intent="conversation",

            workspace="general",

            priority="normal",

            action="reply",

            reason="General conversation."

        )


if __name__ == "__main__":

    interpreter = NaturalTeachingInterpreter()

    examples = [

        "Teach this cocktail for the competition.",

        "Business meeting tomorrow with client.",

        "Always remember this recipe.",

        "Don't remember this conversation.",

        "Hello Jessie, how are you?"

    ]

    print("===== NATURAL TEACHING INTERPRETER =====")

    print()

    for item in examples:

        print("Input :", item)

        print(interpreter.interpret(item))

        print("-" * 70)