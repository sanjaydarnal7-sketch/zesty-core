"""
Zesty OS
Conversation Engine
Version: 1.0

Mission 43

Coordinates the complete conversation flow
between the user and all Zesty intelligence
modules.
"""

from dataclasses import dataclass

from core.personality_engine import PersonalityEngine
from core.natural_teaching_interpreter import NaturalTeachingInterpreter
from core.memory_router import MemoryRouter
from core.brain import CoreBrain
from core.executive_response_engine import ExecutiveResponseEngine
from core.action_planner import ExecutiveActionPlanner
from core.intelligence_pipeline import IntelligencePipeline


@dataclass
class ConversationResult:

    personality: object

    teaching: object

    memory: object

    brain: dict

    executive_response: object

    action_plan: object


class ConversationEngine:

    def __init__(self):

        self.personality = PersonalityEngine()

        self.teacher = NaturalTeachingInterpreter()

        self.memory = MemoryRouter()

        self.brain = CoreBrain()

        self.pipeline = IntelligencePipeline()

        self.response = ExecutiveResponseEngine()

        self.actions = ExecutiveActionPlanner()

    def process(self, message: str):

        personality = self.personality.select(message)

        teaching = self.teacher.interpret(message)

        memory = self.memory.route(message)

        brain = self.brain.process(message)

        pipeline = self.pipeline.process(

            message,

            message

        )

        executive = self.response.build(pipeline)

        plan = self.actions.build(pipeline)

        return ConversationResult(

            personality=personality,

            teaching=teaching,

            memory=memory,

            brain=brain,

            executive_response=executive,

            action_plan=plan

        )


if __name__ == "__main__":

    engine = ConversationEngine()

    result = engine.process(

        "Create a cocktail recipe for the competition."

    )

    print("===== CONVERSATION ENGINE =====")

    print()

    print("PERSONALITY")

    print(result.personality)

    print()

    print("TEACHING")

    print(result.teaching)

    print()

    print("MEMORY")

    print(result.memory)

    print()

    print("BRAIN")

    print(result.brain)

    print()

    print("EXECUTIVE")

    print(result.executive_response)

    print()

    print("ACTION PLAN")

    for action in result.action_plan.list_all():

        print(action)