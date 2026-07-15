"""
Zesty OS
Memory Router
Version: 1.0

Mission 36

Decides whether information should be stored
as long-term memory.
"""

from dataclasses import dataclass


@dataclass
class MemoryDecision:

    should_store: bool

    reason: str

    category: str


class MemoryPolicy:

    STORE_CATEGORIES = {

        "business",
        "project",
        "recipe",
        "asset",
        "framework",
        "goal",
        "client",
        "preference",
        "family",
        "friend"

    }

    IGNORE_WORDS = {

        "hi",
        "hello",
        "hey",
        "thanks",
        "thank you",
        "bye",
        "ok",
        "okay"

    }

    def evaluate(
        self,
        category: str,
        text: str
    ) -> MemoryDecision:

        message = text.lower().strip()

        if message in self.IGNORE_WORDS:

            return MemoryDecision(

                should_store=False,

                reason="Greeting or temporary conversation.",

                category=category

            )

        if category.lower() in self.STORE_CATEGORIES:

            return MemoryDecision(

                should_store=True,

                reason="Important long-term information.",

                category=category

            )

        return MemoryDecision(

            should_store=False,

            reason="Not useful for long-term memory.",

            category=category

        )


class MemoryRouter:

    def __init__(self):

        self.policy = MemoryPolicy()

    def route(
        self,
        category: str,
        text: str
    ) -> MemoryDecision:

        return self.policy.evaluate(

            category,

            text

        )


if __name__ == "__main__":

    router = MemoryRouter()

    tests = [

        ("business", "Sector Gin Collaboration"),

        ("recipe", "Negroni Recipe"),

        ("general", "Hello"),

        ("general", "Thanks"),

        ("goal", "Reach one crore revenue"),

        ("project", "Zesty Executive Dashboard")

    ]

    print("===== MEMORY ROUTER =====")

    print()

    for category, text in tests:

        result = router.route(

            category,

            text

        )

        print(f"Input : {text}")

        print(result)

        print("-" * 60)