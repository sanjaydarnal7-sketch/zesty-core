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
            "terminal", "git", "github", "docker",
            "ollama", "llm", "prompt", "refactor",
            "debug", "compile", "syntax",
        )

        reasoning = (
            "think", "reason", "analyze", "architecture",
            "design", "plan", "strategy",
            "compare", "pros", "cons",
            "decision", "roadmap", "optimize",
            "evaluate", "tradeoff",
        )

        if any(word in text for word in reasoning):
            return "reasoning"

        if text.startswith((
            "/",
            "run ",
            "execute ",
            "build ",
            "create ",
        )):
            return "coding"

        if any(word in text for word in coding):
            return "coding"

        return "conversation"
