"""Hindi voice post-processing — feminine partner tone for Zesty (Ishita)."""

from __future__ import annotations

import re

# Masculine → feminine verb forms (Zesty is female)
_FEMININE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"सकता\s+हूँ", "सकती हूँ"),
    (r"सकता\s+हूं", "सकती हूं"),
    (r"सकता\s+हूं?", "सकती हूँ"),
    (r"करता\s+हूँ", "करती हूँ"),
    (r"करता\s+हूं", "करती हूं"),
    (r"बोलता\s+हूँ", "बोलती हूँ"),
    (r"बोलता\s+हूं", "बोलती हूं"),
    (r"देता\s+हूँ", "देती हूँ"),
    (r"देता\s+हूं", "देती हूं"),
    (r"जाता\s+हूँ", "जाती हूँ"),
    (r"जाता\s+हूं", "जाती हूं"),
    (r"रहता\s+हूँ", "रहती हूँ"),
    (r"रहता\s+हूं", "रहती हूं"),
    (r"लगता\s+हूँ", "लगती हूँ"),
    (r"लगता\s+हूं", "लगती हूं"),
    (r"देख\s+सकता\s+हूँ", "देख सकती हूँ"),
    (r"देख\s+सकता\s+हूं", "देख सकती हूं"),
    (r"हूँ\s+नहीं", "हूँ नहीं"),  # already feminine for negative
    (r"हूं\s+नहीं", "हूँ नहीं"),
    (r"नहीं\s+हूँ", "नहीं हूँ"),
    (r"नहीं\s+हूं", "नहीं हूँ"),
)

# Formal आप → casual तुम (partner tone; skip when user quoted formal speech)
_TUM_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bआपका\b", "तुम्हारा"),
    (r"\bआपकी\b", "तुम्हारी"),
    (r"\bआपके\b", "तुम्हारे"),
    (r"\bआपको\b", "तुम्हें"),
    (r"\bआपसे\b", "तुमसे"),
    (r"\bआपने\b", "तुमने"),
    (r"\bआप\b", "तुम"),
)


def apply_hindi_partner_voice(text: str) -> str:
    """Force feminine verb forms and casual तुम address in Hindi replies."""
    out = (text or "").strip()
    if not out:
        return out
    if not re.search(r"[\u0900-\u097F]", out):
        return out

    for pattern, repl in _FEMININE_REPLACEMENTS:
        out = re.sub(pattern, repl, out)
    for pattern, repl in _TUM_REPLACEMENTS:
        out = re.sub(pattern, repl, out)
    return out
