"""Shared text normalization for all TTS providers."""

from __future__ import annotations

import os
import re

from tts.lang_detect import detect_speech_language

_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def normalize_for_tts(text: str) -> str:
    """Strip markdown/meta and flatten text for speech synthesis."""
    if not text:
        return ""

    normalized = text.strip()
    normalized = re.sub(r"\*{1,2}(.*?)\*{1,2}", r"\1", normalized)
    normalized = re.sub(r"^#{1,6}\s+", "", normalized, flags=re.MULTILINE)
    normalized = re.sub(r"^[-•]\s+", "", normalized, flags=re.MULTILINE)
    normalized = re.sub(r"<[^>]+>", "", normalized)
    normalized = re.sub(r"\[TARGET_PANEL:\s*[A-Za-z_]+\]", "", normalized).strip()
    normalized = re.sub(r"\.{3,}", "...", normalized)
    normalized = re.sub(r"([.,!?])([^\s])", r"\1 \2", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    lines = [line.strip() for line in normalized.split("\n") if line.strip()]
    return " ".join(lines)


# Younger female Bulbul v3 — Ishita (Entertainment / Dynamic).
_SPEAKER_DEFAULT = "ishita"
_SPEAKER_EN_YOUNG = "ishita"
_SPEAKER_HI_YOUNG = "ishita"
_SPEAKER_HINGLISH_YOUNG = "ishita"


def resolve_sarvam_config(text: str, lang_hint: str = "english") -> tuple[str, str]:
    """
    Pick Sarvam ``language_code`` + ``speaker`` from reply text + session language.

    - English replies → ``en-IN`` + kavya
    - Hindi (Devanagari) → ``hi-IN`` + neha
    - Hinglish / Roman Hindi mix → ``hi-IN`` (Bulbul code-switch) + neha
    """
    override = os.environ.get("SARVAM_TTS_SPEAKER", "").strip()
    speaker_en = os.environ.get("SARVAM_TTS_SPEAKER_EN", _SPEAKER_EN_YOUNG)
    speaker_hi = os.environ.get("SARVAM_TTS_SPEAKER_HI", _SPEAKER_HI_YOUNG)
    speaker_hinglish = os.environ.get(
        "SARVAM_TTS_SPEAKER_HINGLISH", _SPEAKER_HINGLISH_YOUNG
    )

    dialect = detect_speech_language(text, lang_hint)

    if dialect == "english":
        return "en-IN", override or speaker_en
    if dialect == "hindi":
        return "hi-IN", override or speaker_hi
    return "hi-IN", override or speaker_hinglish


def resolve_lang_code(text: str, lang_hint: str = "english") -> str:
    """Legacy alias — returns BCP-47 language code."""
    return resolve_sarvam_config(text, lang_hint)[0]
