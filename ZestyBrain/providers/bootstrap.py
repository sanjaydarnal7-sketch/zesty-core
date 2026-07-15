"""
Zesty OS
Provider Bootstrap
Version: 1.0

Mission 14
Loads all AI providers into the registry.
"""

from providers.registry import Provider


class ProviderBootstrap:

    def load(self, registry):

        providers = [

            Provider(
                name="Grok",
                provider_type="Cloud",
                internet=True,
                local=False,
                vision=True,
                enabled=True,
                priority=1
            ),

            Provider(
                name="Ollama",
                provider_type="Local",
                internet=False,
                local=True,
                vision=False,
                enabled=True,
                priority=2
            ),

            Provider(
                name="LM Studio",
                provider_type="Local",
                internet=False,
                local=True,
                vision=False,
                enabled=True,
                priority=3
            )

        ]

        for provider in providers:
            registry.register(provider)

        return registry


if __name__ == "__main__":

    from providers.registry import ProviderRegistry

    registry = ProviderRegistry()

    bootstrap = ProviderBootstrap()

    bootstrap.load(registry)

    print("===== BOOTSTRAP COMPLETE =====")

    for provider in registry.list_all():
        print(f"✅ {provider.name}")