"""
Zesty OS
Intelligence Pipeline
Version: 1.0

Mission 33

Orchestrates all intelligence engines.
"""

from core.knowledge_engine import KnowledgeEngine
from core.recommendation_engine import RecommendationEngine
from core.guardian_engine import GuardianEngine
from core.asset_manager import AssetManager, Asset


class IntelligencePipeline:

    def __init__(self):

        self.knowledge = KnowledgeEngine()

        self.recommendation = RecommendationEngine()

        self.guardian = GuardianEngine()

        self.assets = AssetManager()

        self._load_default_assets()

    def _load_default_assets(self):

        self.assets.register(

            Asset(

                name="MacBook Air M4",

                asset_type="Device",

                category="Computer",

                status="Active",

                owner="Sanjay",

                metadata={

                    "purpose": "Zesty Development"

                }

            )

        )

    def process(self, title: str, content: str):

        knowledge = self.knowledge.classify(title, content)

        recommendation = self.recommendation.recommend(
            knowledge.category
        )

        guardian = self.guardian.evaluate(
            knowledge.category
        )

        return {

            "knowledge": knowledge,

            "recommendation": recommendation,

            "guardian": guardian

        }


if __name__ == "__main__":

    pipeline = IntelligencePipeline()

    result = pipeline.process(

        "Negroni Recipe",

        "Classic gin cocktail with Campari."

    )

    print(result)