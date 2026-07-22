"""
Language preference detection for Zesty.
"""

from __future__ import annotations

import re


HINGLISH_HINTS = {
    "bro","buddy","bhai","yaar","okay","ok","acha","accha",
    "haan","han","nahi","nah","please","chal","chalo",
    "scene","plan","done","let's","lets","brother"
}


def detect(text: str) -> str:

    text = text.strip()

    if not text:
        return "english"

    hindi = sum("\u0900" <= c <= "\u097F" for c in text)
    english = sum(c.isascii() and c.isalpha() for c in text)

    words = {
        w.lower()
        for w in re.findall(r"[A-Za-z']+", text)
    }

    if hindi and english:
        return "hinglish"

    if hindi and words & HINGLISH_HINTS:
        return "hinglish"

    if hindi:
        return "hindi"

    return "english"
