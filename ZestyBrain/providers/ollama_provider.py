"""
Ollama Provider
"""

from __future__ import annotations

import requests

from .base_provider import BaseProvider
from ZestyBrain.persona.history_sanitizer import HistorySanitizer


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(
        self,
        default_model: str = "qwen2.5:3b",
        host: str = "http://127.0.0.1:11434",
    ) -> None:
        self.default_model = default_model
        self.host = host.rstrip("/")
        self.history_sanitizer = HistorySanitizer()

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
        temperature: float = 0.82,
        max_tokens: int = 2048,
        **kwargs,
    ) -> str:

        model = kwargs.get("model", self.default_model)
        history = kwargs.get("messages", [])
        history = self.history_sanitizer.sanitize(history)

        history = [
            m for m in history
            if m.get("content", "").strip()
        ]

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
                    "top_p": 0.95,
                    "top_k": 60,
                    "repeat_penalty": 1.08,
                    "num_ctx": 16384,
                    "num_predict": max_tokens,
                },
            },
            timeout=300,
        )

        response.raise_for_status()

        return response.json()["message"]["content"].strip()
