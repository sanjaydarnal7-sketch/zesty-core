from __future__ import annotations

from .providers.bootstrap import ProviderBootstrap
from .providers.registry import ProviderRegistry
from .routing.model_router import ModelRouter

from .persona.persona_engine import PersonaEngine
from .persona.persona_pipeline import PersonaPipeline

from .memory.memory_engine import MemoryEngine
from .memory.memory_pipeline import MemoryPipeline
from .memory.fact_memory import FactMemory


class RuntimeManager:

    def __init__(self) -> None:

        self.registry = ProviderRegistry()
        ProviderBootstrap.initialize(self.registry)

        self.persona = PersonaEngine()
        self.persona_pipeline = PersonaPipeline()

        self.memory = MemoryEngine()

        self.facts = FactMemory()

        self.pipeline = MemoryPipeline(
            memory=self.memory,
            facts=self.facts,
        )

        provider = self.registry.get("ollama")

        if provider is None:
            raise RuntimeError("Ollama provider is not registered.")

        self.router = ModelRouter(provider)

    @property
    def provider(self):
        return self.router.provider

    def is_ready(self) -> bool:
        return self.provider.is_available()

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> str:

        self.pipeline.process(prompt)

        persona_context = self.persona_pipeline.process(prompt)

        memory_context = self.memory.context()

        fact_context = self.facts.prompt_context()

        if fact_context.strip():

            if memory_context.strip():
                memory_context += "\n\n"

            memory_context += fact_context

        persona_prompt = self.persona.build_system_prompt(
            user_prompt=prompt,
            memory_context=memory_context,
            language=persona_context.language,
            behavior=persona_context.behavior,
            learning=persona_context.learning,
        )

        if system_prompt:
            system_prompt = (
                persona_prompt
                + "\n\n"
                + system_prompt
            )
        else:
            system_prompt = persona_prompt

        print("\n" + "=" * 70)
        print("🧠 PERSONA SYSTEM PROMPT")
        print("-" * 70)
        print(system_prompt)
        print("=" * 70 + "\n")

        reply = self.router.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=self.memory.messages(),
            **kwargs,
        )

        self.memory.remember(
            f"Zesty: {reply}"
        )

        self.pipeline.process(reply)

        return reply
