"""
Language preference detection.
"""

def detect(text: str) -> str:
    text = text.strip()

    hindi = sum('\u0900' <= c <= '\u097F' for c in text)
    english = sum(c.isascii() and c.isalpha() for c in text)

    if hindi > 0 and english > 0:
        return "hinglish"

    if hindi > 0:
        return "hindi"

    return "english"
