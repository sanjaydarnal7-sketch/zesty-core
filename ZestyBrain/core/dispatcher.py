"""
Zesty OS Dispatcher
Version: 1.0

The Dispatcher decides which subsystem should handle a request.
"""

from dataclasses import dataclass


@dataclass
class DispatchDecision:
    target: str
    reason: str


class Dispatcher:

    def dispatch(self, text: str) -> DispatchDecision:

        message = text.lower()

        if any(word in message for word in [
            "client",
            "meeting",
            "proposal",
            "business"
        ]):
            return DispatchDecision(
                target="memory",
                reason="Business memory detected"
            )

        if any(word in message for word in [
            "instagram",
            "youtube",
            "trend",
            "news"
        ]):
            return DispatchDecision(
                target="cloud_ai",
                reason="Latest information required"
            )

        if any(word in message for word in [
            "summarize",
            "analyse",
            "analyze",
            "recipe"
        ]):
            return DispatchDecision(
                target="local_ai",
                reason="Local reasoning task"
            )

        return DispatchDecision(
            target="brain",
            reason="General request"
        )


if __name__ == "__main__":

    dispatcher = Dispatcher()

    tests = [

        "New client meeting today",

        "Latest Instagram trends",

        "Summarize this recipe",

        "Hello Zesty"

    ]

    for item in tests:

        result = dispatcher.dispatch(item)

        print(f"{item}")

        print(result)

        print("-" * 40)