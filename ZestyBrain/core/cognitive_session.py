"""
Zesty OS
Cognitive Session
Version: 1.0

Mission 37

Maintains the current working context
for the active conversation.

Unlike the Memory Engine, this information
exists only for the current session.
"""

from dataclasses import dataclass


@dataclass
class CognitiveSession:

    current_project: str | None = None

    current_client: str | None = None

    current_framework: str | None = None

    current_goal: str | None = None

    current_topic: str | None = None

    active_task: str | None = None


class CognitiveSessionManager:

    def __init__(self):

        self.session = CognitiveSession()

    def update(
        self,
        *,
        project=None,
        client=None,
        framework=None,
        goal=None,
        topic=None,
        task=None
    ):

        if project is not None:
            self.session.current_project = project

        if client is not None:
            self.session.current_client = client

        if framework is not None:
            self.session.current_framework = framework

        if goal is not None:
            self.session.current_goal = goal

        if topic is not None:
            self.session.current_topic = topic

        if task is not None:
            self.session.active_task = task

    def get(self):

        return self.session

    def clear(self):

        self.session = CognitiveSession()


if __name__ == "__main__":

    manager = CognitiveSessionManager()

    manager.update(

        project="Zesty OS",

        client="Craftsmen & Co",

        framework="Flavor DNA",

        goal="Build Executive AI",

        topic="Memory System",

        task="Mission 37"

    )

    print("===== COGNITIVE SESSION =====")

    print()

    print(manager.get())

    print()

    manager.clear()

    print("===== AFTER CLEAR =====")

    print()

    print(manager.get())