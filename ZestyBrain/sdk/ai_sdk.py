"""
Zesty OS
AI SDK
Version: 1.0

Mission 21

Universal interface for all AI providers.
"""

from core.runtime.manager import RuntimeManager


class AISDK:

    def __init__(self):

        self.runtime = RuntimeManager()

    def generate(self, prompt: str):

        return self.runtime.execute(prompt)

    def provider(self):

        return self.runtime.get_active_provider()


if __name__ == "__main__":

    sdk = AISDK()

    print(

        sdk.generate(

            "Hello Zesty"

        )

    )