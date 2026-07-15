"""
ZestyBrain Memory Router
Version 1.0

Purpose:
Detect which category a memory belongs to.
"""

class MemoryRouter:

    def __init__(self):
        pass

    def detect_category(self, text):

        text = text.lower()

        rules = {

            "Business": [
                "business",
                "company",
                "client meeting",
                "consultancy",
                "bar",
                "cocktail",
                "menu",
                "project proposal",
                "invoice"
            ],

            "Clients": [
                "client",
                "customer",
                "meeting",
                "contract"
            ],

            "Journal": [
                "today",
                "feeling",
                "journal",
                "diary",
                "my day"
            ],

            "Projects": [
                "project",
                "software",
                "app",
                "zesty",
                "jarvis",
                "ai"
            ],

            "Recipes": [
                "recipe",
                "ingredient",
                "cocktail",
                "drink"
            ],

            "Knowledge": [
                "learn",
                "research",
                "study",
                "knowledge"
            ],

            "Family": [
                "mother",
                "father",
                "brother",
                "sister",
                "family"
            ],

            "Friends": [
                "friend",
                "buddy"
            ],

            "Social": [
                "instagram",
                "linkedin",
                "youtube",
                "facebook"
            ]
        }

        for category, keywords in rules.items():

            for word in keywords:

                if word in text:
                    return category

        return "Journal"


if __name__ == "__main__":

    router = MemoryRouter()

    print(router.detect_category(
        "Today I met a new client for cocktail consultancy."
    ))