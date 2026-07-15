"""
Zesty OS
Executive Response Engine
Version: 1.0

Mission 38

Transforms structured intelligence into
a human-friendly executive response.
"""

from dataclasses import dataclass


@dataclass
class ExecutiveResponse:

    request_type: str

    summary: str

    recommendation: str

    safety: str

    status: str


class ExecutiveResponseEngine:

    def build(self, pipeline_result):

        knowledge = pipeline_result["knowledge"]

        recommendation = pipeline_result["recommendation"]

        guardian = pipeline_result["guardian"]

        return ExecutiveResponse(

            request_type=knowledge.category.title(),

            summary=f"Detected {knowledge.category} request.",

            recommendation=recommendation.message,

            safety=guardian.recommended_action,

            status="Ready"

        )

    def format(self, response: ExecutiveResponse):

        return f"""
========================================
        EXECUTIVE SUMMARY
========================================

Request Type
------------
{response.request_type}

Summary
-------
{response.summary}

Recommendation
--------------
{response.recommendation}

Safety
------
{response.safety}

Status
------
{response.status}

========================================
"""


if __name__ == "__main__":

    from core.intelligence_pipeline import IntelligencePipeline

    pipeline = IntelligencePipeline()

    result = pipeline.process(

        "Negroni Recipe",

        "Classic gin cocktail with Campari."

    )

    engine = ExecutiveResponseEngine()

    response = engine.build(result)

    print(engine.format(response))