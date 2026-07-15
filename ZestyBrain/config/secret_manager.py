"""
Zesty OS
Secret Manager
Version: 1.0

Mission 15

Responsible for:
- Store Secrets
- Read Secrets
- Delete Secrets
- List Available Secrets
"""

import json
from pathlib import Path


class SecretManager:

    def __init__(self):

        self.root = Path(__file__).parent

        self.secret_file = self.root / "secrets.json"

        if not self.secret_file.exists():

            with open(self.secret_file, "w", encoding="utf-8") as f:

                json.dump({}, f, indent=4)

    def _load(self):

        with open(self.secret_file, "r", encoding="utf-8") as f:

            return json.load(f)

    def _save(self, data):

        with open(self.secret_file, "w", encoding="utf-8") as f:

            json.dump(data, f, indent=4)

    def set_secret(self, name, value):

        data = self._load()

        data[name] = value

        self._save(data)

    def get_secret(self, name):

        data = self._load()

        return data.get(name)

    def delete_secret(self, name):

        data = self._load()

        if name in data:

            del data[name]

            self._save(data)

    def list_secrets(self):

        data = self._load()

        return list(data.keys())


if __name__ == "__main__":

    manager = SecretManager()

    manager.set_secret(
        "grok_api",
        "YOUR_API_KEY"
    )

    print(manager.get_secret("grok_api"))

    print(manager.list_secrets())