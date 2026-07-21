"""
Model Router
"""

from __future__ import annotations

from ZestyBrain.providers.base_provider import BaseProvider
from .intent_classifier import IntentClassifier


class ModelRouter:

    def __init__(self, provider: BaseProvider):
        self.provider = provider
        self.classifier = IntentClassifier()

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> str:

        intent = self.classifier.classify(prompt)

        model_map = {
            "conversation": "llama3.2:3b",
            "coding": "qwen2.5:7b-instruct",
            "reasoning": "deepseek-r1:8b",
        }

        model = model_map.get(intent, "llama3.2:3b")

        return self.provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            messages=kwargs.get("messages", []),
        )
