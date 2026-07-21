"""
Ollama Provider
"""

from __future__ import annotations

import requests

from .base_provider import BaseProvider


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(
        self,
        default_model: str = "llama3.2:3b",
        host: str = "http://127.0.0.1:11434",
    ) -> None:
        self.default_model = default_model
        self.host = host.rstrip("/")

    def is_available(self) -> bool:
        try:
            return requests.get(f"{self.host}/api/tags", timeout=3).ok
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> str:

        model = kwargs.get("model", self.default_model)
        history = kwargs.get("messages", [])

        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
            })

        messages.extend(history)

        messages.append({
            "role": "user",
            "content": prompt,
        })

        print(f"[OLLAMA] model={model}")
        print(f"[OLLAMA] messages={len(messages)}")

        response = requests.post(
            f"{self.host}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
            timeout=300,
        )

        response.raise_for_status()

        return response.json()["message"]["content"].strip()
