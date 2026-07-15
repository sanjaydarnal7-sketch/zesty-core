"""
Zesty OS
Core Brain
Version: 3.0

Mission 34

Master Orchestrator
"""

from core.dispatcher import Dispatcher
from core.intelligence_pipeline import IntelligencePipeline


class CoreBrain:

    def __init__(self):

        self.dispatcher = Dispatcher()

        self.pipeline = IntelligencePipeline()

    def process(self, text: str):

        # Step 1
        decision = self.dispatcher.dispatch(text)

        # Step 2
        pipeline = self.pipeline.process(

            title=text,

            content=text

        )

        # Step 3
        return {

            "user_input": text,

            "dispatcher": {

                "target": decision.target,

                "reason": decision.reason

            },

            "knowledge": pipeline["knowledge"],

            "recommendation": pipeline["recommendation"],

            "guardian": pipeline["guardian"]

        }


if __name__ == "__main__":

    brain = CoreBrain()

    result = brain.process(

        "Create a gin cocktail recipe"

    )

    print(result)