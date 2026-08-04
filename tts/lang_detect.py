"""Detect spoken language from reply text — mirrors Zesty session language rules."""

from __future__ import annotations

import re

from conversation_manager.models import _HINGLISH_MARKERS

_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def detect_speech_language(text: str, session_hint: str = "english") -> str:
    """
    Return ``english`` | ``hindi`` | ``hinglish`` for TTS routing.

    Uses the reply text first (what Zesty actually said), then session hint.
    """
    raw = (text or "").strip()
    if not raw:
        return _normalize_hint(session_hint)

    devanagari = len(_DEVANAGARI_RE.findall(raw))
    latin = len(re.findall(r"[A-Za-z]", raw))
    total_letters = devanagari + latin

    if total_letters == 0:
        return _normalize_hint(session_hint)

    if devanagari / total_letters >= 0.35:
        return "hindi"

    has_hinglish = bool(_HINGLISH_MARKERS.search(raw))
    ascii_only = bool(re.match(r"^[\x00-\x7F]+$", raw))

    if has_hinglish:
        return "hinglish"
    if devanagari > 0 and latin > 0:
        return "hinglish"
    if ascii_only and latin > 0:
        return "english"

    hint = _normalize_hint(session_hint)
    if hint in ("hindi", "hinglish"):
        return hint
    return "hinglish" if devanagari > 0 else "english"


def _normalize_hint(hint: str) -> str:
    h = (hint or "english").lower()
    if h in ("en", "english"):
        return "english"
    if h in ("hi", "hindi"):
        return "hindi"
    if h == "hinglish":
        return "hinglish"
    return "english"
