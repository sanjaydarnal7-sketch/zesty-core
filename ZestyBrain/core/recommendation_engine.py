"""
Zesty OS
Recommendation Engine
Version: 1.0

Mission 30

Provides recommended next actions based on knowledge category.
"""

from dataclasses import dataclass


@dataclass
class Recommendation:

    category: str
    workflow: list[str]
    message: str


class RecommendationEngine:

    def recommend(self, category: str) -> Recommendation:

        category = category.lower()

        workflows = {

            "recipe": [
                "Research Ingredients",
                "Flavor DNA Analysis",
                "Technique Selection",
                "Sensory Evaluation",
                "Presentation",
                "Commercial Validation"
            ],

            "business": [
                "Research Client",
                "Define Objective",
                "Prepare Proposal",
                "Execution Plan",
                "Follow-up"
            ],

            "trading": [
                "Astro Analysis",
                "Fundamental Analysis",
                "Technical Analysis",
                "Risk Management",
                "Trade Execution",
                "Journal Review"
            ],

            "project": [
                "Define Goal",
                "Planning",
                "Execution",
                "Testing",
                "Review"
            ],

            "people": [
                "Review Relationship Context",
                "Recall Previous Conversations",
                "Suggest Best Communication"
            ],

            "general": [
                "Gather Information",
                "Analyze",
                "Recommend Next Step"
            ]
        }

        workflow = workflows.get(
            category,
            workflows["general"]
        )

        return Recommendation(
            category=category,
            workflow=workflow,
            message=f"Recommended workflow prepared for '{category}'."
        )


if __name__ == "__main__":

    engine = RecommendationEngine()

    result = engine.recommend("recipe")

    print(result)