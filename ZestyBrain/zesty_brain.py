"""
ZestyBrain Core
Version: 1.0
"""

from pathlib import Path
import json


class ZestyBrain:

    def __init__(self):

        self.root = Path(__file__).parent
        self.vault = self.root / "vault"
        self.schemas = self.root / "schemas"
        self.memory_schema = self.schemas / "memory_schema.json"

        print("✅ ZestyBrain Loaded")

    def load_schema(self):

        with open(self.memory_schema, "r") as f:
            return json.load(f)

    def list_categories(self):

        return [
            folder.name
            for folder in self.vault.iterdir()
            if folder.is_dir()
        ]

    def save_memory(self, category, filename, content):

        folder = self.vault / category
        folder.mkdir(exist_ok=True)

        file_path = folder / f"{filename}.md"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Memory Saved: {file_path}")


if __name__ == "__main__":

    brain = ZestyBrain()

    print(brain.list_categories())

    brain.save_memory(
        "Journal",
        "First_Test",
        "# First Memory\n\nThis is my first ZestyBrain memory."
    )