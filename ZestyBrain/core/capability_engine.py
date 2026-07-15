"""
Zesty OS
Capability Engine
Version: 1.0

Mission 22

Routes requests by capability instead of provider.
"""

from sdk.ai_sdk import AISDK


class CapabilityEngine:

    def __init__(self):

        self.sdk = AISDK()

    def execute(
        self,
        capability: str,
        prompt: str
    ):

        capability = capability.lower()

        capability_map = {

            "reasoning": self._reasoning,

            "chat": self._reasoning,

            "general": self._reasoning,

        }

        handler = capability_map.get(
            capability,
            self._reasoning
        )

        return handler(prompt)

    def _reasoning(self, prompt: str):

        return self.sdk.generate(prompt)


if __name__ == "__main__":

    engine = CapabilityEngine()

    result = engine.execute(

        capability="reasoning",

        prompt="Hello Zesty"

    )

    print(result)
    