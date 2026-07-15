"""
Zesty OS
Provider Registry
Version: 1.0

This registry manages all AI providers.
"""

from dataclasses import dataclass


@dataclass
class Provider:

    name: str

    provider_type: str

    internet: bool

    local: bool

    vision: bool

    enabled: bool

    priority: int


class ProviderRegistry:

    def __init__(self):

        self.providers = {}

    def register(self, provider: Provider):

        self.providers[provider.name.lower()] = provider

    def get(self, name):

        return self.providers.get(name.lower())

    def list_all(self):

        return list(self.providers.values())


if __name__ == "__main__":

    registry = ProviderRegistry()

    registry.register(

        Provider(

            name="Grok",

            provider_type="Cloud",

            internet=True,

            local=False,

            vision=True,

            enabled=True,

            priority=1

        )

    )

    registry.register(

        Provider(

            name="Ollama",

            provider_type="Local",

            internet=False,

            local=True,

            vision=False,

            enabled=True,

            priority=2

        )

    )

    registry.register(

        Provider(

            name="LM Studio",

            provider_type="Local",

            internet=False,

            local=True,

            vision=False,

            enabled=True,

            priority=3

        )

    )

    print("===== REGISTERED PROVIDERS =====")

    for provider in registry.list_all():

        print(provider)