"""
ZestyBrain Brain Pipeline
Version: 1.0

This module is the entry point for every memory request.

Flow:

User
 ↓
Brain Pipeline
 ↓
Memory Router
 ↓
ZestyBrain
 ↓
Vault
"""

from memory_router import MemoryRouter
from zesty_brain import ZestyBrain


class BrainPipeline:

    def __init__(self):

        self.router = MemoryRouter()
        self.brain = ZestyBrain()

    def process_memory(self, filename, text):

        category = self.router.detect_category(text)

        self.brain.save_memory(
            category=category,
            filename=filename,
            content=text
        )

        return {
            "status": "success",
            "category": category,
            "filename": filename
        }


if __name__ == "__main__":

    pipeline = BrainPipeline()

    result = pipeline.process_memory(

        filename="Mission_6_Test",

        text="""
Today I met a new client.
We discussed cocktail consultancy
for a luxury hotel.
"""

    )

    print(result)