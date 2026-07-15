"""
Zesty OS
Guardian Engine
Version: 1.0

Mission 31

Detects important situations and decides
whether Jessie should observe, recommend,
warn, or protect.
"""

from dataclasses import dataclass


@dataclass
class GuardianAlert:

    level: str
    title: str
    message: str
    recommended_action: str
    requires_confirmation: bool


class GuardianEngine:

    def evaluate(self, category: str) -> GuardianAlert:

        category = category.lower()

        rules = {

            "recipe": GuardianAlert(
                level="recommend",
                title="Recipe Review",
                message="Recipe should be validated before execution.",
                recommended_action="Run Flavor DNA workflow.",
                requires_confirmation=False
            ),

            "business": GuardianAlert(
                level="warn",
                title="Business Opportunity",
                message="Business actions should be reviewed carefully.",
                recommended_action="Review proposal before sending.",
                requires_confirmation=True
            ),

            "trading": GuardianAlert(
                level="warn",
                title="Trading Risk",
                message="Trading decisions involve financial risk.",
                recommended_action="Perform risk analysis before execution.",
                requires_confirmation=True
            ),

            "project": GuardianAlert(
                level="observe",
                title="Project Monitoring",
                message="Project progress is being monitored.",
                recommended_action="Continue working.",
                requires_confirmation=False
            ),

            "people": GuardianAlert(
                level="recommend",
                title="Relationship Reminder",
                message="Communication may strengthen the relationship.",
                recommended_action="Consider reaching out.",
                requires_confirmation=False
            ),

            "general": GuardianAlert(
                level="observe",
                title="General Request",
                message="No immediate risks detected.",
                recommended_action="Proceed normally.",
                requires_confirmation=False
            )
        }

        return rules.get(category, rules["general"])


if __name__ == "__main__":

    engine = GuardianEngine()

    alert = engine.evaluate("business")

    print(alert)