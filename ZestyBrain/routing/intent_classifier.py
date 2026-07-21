"""
Intent Classifier
"""

from __future__ import annotations


class IntentClassifier:

    def classify(self, prompt: str) -> str:
        text = prompt.lower()

        coding = (
            "python", "code", "bug", "function", "class",
            "api", "json", "sql", "javascript", "flutter",
            "react", "fix", "error",
        )

        reasoning = (
            "think", "reason", "analyze", "architecture",
            "design", "plan", "strategy",
        )

        if any(word in text for word in reasoning):
            return "reasoning"

        if any(word in text for word in coding):
            return "coding"

        return "conversation"
