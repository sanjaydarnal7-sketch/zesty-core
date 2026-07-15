"""
Zesty OS
Context Engine
Version: 1.0

Mission 25

Builds active execution context.
"""


class ContextEngine:

    def __init__(self):

        self.active_project = ""

        self.local_context = ""

        self.web_context = ""

    def set_project(self, project: str):

        self.active_project = project

    def set_local_context(self, context: str):

        self.local_context = context

    def set_web_context(self, context: str):

        self.web_context = context

    def build(self):

        return {

            "project": self.active_project,

            "local_context": self.local_context,

            "web_context": self.web_context

        }


if __name__ == "__main__":

    context = ContextEngine()

    context.set_project("Zesty OS")

    context.set_local_context("Working on Mission 25")

    context.set_web_context("")

    print(

        context.build()

    )