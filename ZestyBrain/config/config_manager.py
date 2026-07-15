"""
Zesty OS
Configuration Manager
Version: 1.0

Responsible for:
- Loading Settings
- Saving Settings
- Managing AI Providers
- Managing Voice Providers
"""

import json
from pathlib import Path


class ConfigManager:

    def __init__(self):

        self.root = Path(__file__).parent

        self.settings_file = self.root / "settings.json"

        self.settings = self.load()

    def load(self):

        if not self.settings_file.exists():

            return {}

        with open(self.settings_file, "r", encoding="utf-8") as f:

            return json.load(f)

    def save(self):

        with open(self.settings_file, "w", encoding="utf-8") as f:

            json.dump(
                self.settings,
                f,
                indent=4
            )

    def set(self, key, value):

        self.settings[key] = value

        self.save()

    def get(self, key, default=None):

        return self.settings.get(key, default)


if __name__ == "__main__":

    config = ConfigManager()

    config.set("active_provider", "grok")

    config.set("voice_provider", "microsoft")

    print(config.get("active_provider"))

    print(config.get("voice_provider"))