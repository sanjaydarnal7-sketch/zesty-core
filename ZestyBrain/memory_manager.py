"""
ZestyBrain Memory Manager
Version: 1.0

Purpose:
- Decide whether to create a new memory
- Update existing memory
- Save through ZestyBrain
"""

from pathlib import Path

from memory_router import MemoryRouter
from zesty_brain import ZestyBrain


class MemoryManager:

    def __init__(self):

        self.router = MemoryRouter()
        self.brain = ZestyBrain()

    def memory_exists(self, category, filename):

        file_path = (
            self.brain.vault /
            category /
            f"{filename}.md"
        )

        return file_path.exists()

    def save(self, filename, text):

        category = self.router.detect_category(text)

        if self.memory_exists(category, filename):

            print("🟡 Memory already exists.")

            return {
                "status": "exists",
                "category": category,
                "filename": filename
            }

        self.brain.save_memory(
            category,
            filename,
            text
        )

        return {
            "status": "created",
            "category": category,
            "filename": filename
        }


if __name__ == "__main__":

    manager = MemoryManager()

    result = manager.save(

        "Client_Test",

        """
Today I met a new client.

We discussed a cocktail consultancy
project for a luxury hotel.
"""

    )

    print(result)