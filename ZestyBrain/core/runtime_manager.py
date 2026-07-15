"""
Zesty OS
AI Runtime Manager
Version: 1.0

Mission 16

Responsible for:
- Execute AI Tasks
- Select Active Provider
- Read Configuration
- Read Secrets
"""

from config.config_manager import ConfigManager
from config.secret_manager import SecretManager
from providers.registry import ProviderRegistry
from providers.bootstrap import ProviderBootstrap


class RuntimeManager:

    def __init__(self):

        self.config = ConfigManager()

        self.secrets = SecretManager()

        self.registry = ProviderRegistry()

        bootstrap = ProviderBootstrap()

        bootstrap.load(self.registry)

    def get_active_provider(self):

        provider_name = self.config.get(
            "active_provider",
            "grok"
        )

        return self.registry.get(provider_name)

    def execute(self, prompt):

        provider = self.get_active_provider()

        return {

            "provider": provider.name,

            "prompt": prompt,

            "status": "ready",

            "message": "Runtime Manager initialized."

        }


if __name__ == "__main__":

    runtime = RuntimeManager()

    result = runtime.execute(

        "Hello Zesty"

    )

    print(result)