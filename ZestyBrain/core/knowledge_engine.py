"""
Zesty OS
Knowledge Engine
Version: 1.0

Mission 29

Classifies information into structured knowledge categories.
"""

from dataclasses import dataclass


@dataclass
class KnowledgeItem:
    category: str
    title: str
    content: str


class KnowledgeEngine:

    def classify(self, title: str, content: str) -> KnowledgeItem:

        text = f"{title} {content}".lower()

        if any(word in text for word in [
            "cocktail",
            "recipe",
            "ingredient",
            "cordial",
            "flavor"
        ]):
            category = "recipe"

        elif any(word in text for word in [
            "trade",
            "trading",
            "stock",
            "market",
            "forex"
        ]):
            category = "trading"

        elif any(word in text for word in [
            "client",
            "proposal",
            "meeting",
            "business",
            "brand"
        ]):
            category = "business"

        elif any(word in text for word in [
            "project",
            "mission",
            "task"
        ]):
            category = "project"

        elif any(word in text for word in [
            "family",
            "mother",
            "father",
            "friend",
            "partner"
        ]):
            category = "people"

        else:
            category = "general"

        return KnowledgeItem(
            category=category,
            title=title,
            content=content
        )


if __name__ == "__main__":

    engine = KnowledgeEngine()

    item = engine.classify(
        "Negroni Recipe",
        "Classic gin cocktail with Campari."
    )

    print(item)