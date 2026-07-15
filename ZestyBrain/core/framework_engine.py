"""
Zesty OS
Framework Engine
Version: 1.0

Mission 26

Responsible for:
- Register Frameworks
- Load Frameworks
- List Available Frameworks

Future:
- Cocktail Framework
- Trading Framework
- Business Framework
- Research Framework
"""

from typing import Dict


class FrameworkEngine:

    def __init__(self):

        self.frameworks: Dict[str, dict] = {}

    def register(self, name: str, framework: dict):

        self.frameworks[name.lower()] = framework

    def get(self, name: str):

        return self.frameworks.get(name.lower())

    def exists(self, name: str):

        return name.lower() in self.frameworks

    def list_frameworks(self):

        return sorted(self.frameworks.keys())


if __name__ == "__main__":

    engine = FrameworkEngine()

    engine.register(

        "cocktail",

        {

            "steps": [

                "Story",

                "Research",

                "Flavor DNA",

                "Technique",

                "Laboratory",

                "Sensory",

                "Presentation"

            ]

        }

    )

    engine.register(

        "trading",

        {

            "steps": [

                "Astro",

                "Fundamental",

                "Technical",

                "Risk",

                "Execution"

            ]

        }

    )

    print(

        engine.list_frameworks()

    )

    print(

        engine.get("cocktail")

    )