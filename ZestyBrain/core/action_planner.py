"""
Zesty OS
Executive Action Planner
Version: 1.0

Mission 39

Converts executive intelligence into
an actionable execution plan.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class PlannedAction:

    name: str
    description: str
    requires_confirmation: bool = False


@dataclass
class ActionPlan:

    actions: List[PlannedAction] = field(default_factory=list)

    def add(
        self,
        name: str,
        description: str,
        requires_confirmation: bool = False
    ):

        self.actions.append(

            PlannedAction(

                name=name,

                description=description,

                requires_confirmation=requires_confirmation

            )

        )

    def list_all(self):

        return self.actions


class ExecutiveActionPlanner:

    def build(self, pipeline_result):

        knowledge = pipeline_result["knowledge"]

        guardian = pipeline_result["guardian"]

        category = knowledge.category.lower()

        plan = ActionPlan()

        # ---------- Recipe ----------

        if category == "recipe":

            plan.add(

                "Open Framework",

                "Open Flavor DNA framework."

            )

            plan.add(

                "Save Memory",

                "Store recipe development context."

            )

            plan.add(

                "Recipe Validation",

                guardian.recommended_action

            )

        # ---------- Business ----------

        elif category == "business":

            plan.add(

                "Save Memory",

                "Store business discussion."

            )

            plan.add(

                "Update Session",

                "Set current business project."

            )

            plan.add(

                "Request Confirmation",

                "Confirm before external action.",

                True

            )

        # ---------- Project ----------

        elif category == "project":

            plan.add(

                "Update Session",

                "Track current project."

            )

            plan.add(

                "Save Memory",

                "Store project context."

            )

        # ---------- Default ----------

        else:

            plan.add(

                "Reply",

                "Respond to the user."

            )

        return plan


if __name__ == "__main__":

    from core.intelligence_pipeline import IntelligencePipeline

    pipeline = IntelligencePipeline()

    result = pipeline.process(

        "Negroni Recipe",

        "Classic gin cocktail with Campari."

    )

    planner = ExecutiveActionPlanner()

    plan = planner.build(result)

    print("===== EXECUTIVE ACTION PLAN =====")

    print()

    for action in plan.list_all():

        print(action)

        print("-" * 60)