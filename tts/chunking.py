"""Split and cap text for low-latency TTS."""

from __future__ import annotations

import os
import re

# Sentence boundaries for English + Hindi (Devanagari danda).
_SENTENCE_SPLIT = re.compile(r'(?<=[.!?।…])\s+|\n+')

_DEFAULT_MAX_CHARS = 320
_DEFAULT_MAX_SENTENCES = 3


def split_sentences(text: str) -> list[str]:
    """Split text into speakable sentence chunks."""
    text = (text or "").strip()
    if not text:
        return []

    parts = [p.strip() for p in _SENTENCE_SPLIT.split(text) if p.strip()]
    if not parts:
        return [text]

    # Merge very short fragments (e.g. "OK." "Sure.") to avoid tiny TTS calls.
    merged: list[str] = []
    buf = ""
    for part in parts:
        if not buf:
            buf = part
            continue
        if len(buf) < 40 and len(part) < 40:
            buf = f"{buf} {part}"
        else:
            merged.append(buf)
            buf = part
    if buf:
        merged.append(buf)
    return merged


def truncate_for_tts(text: str) -> str:
    """Cap spoken length so long LLM replies don't trigger 60s+ synthesis."""
    max_chars = int(os.environ.get("TTS_MAX_CHARS", os.environ.get("SARVAM_TTS_MAX_CHARS", str(_DEFAULT_MAX_CHARS))))
    max_sentences = int(
        os.environ.get("TTS_MAX_SENTENCES", os.environ.get("SARVAM_TTS_MAX_SENTENCES", str(_DEFAULT_MAX_SENTENCES)))
    )

    sentences = split_sentences(text)
    if not sentences:
        return ""

    kept: list[str] = []
    total = 0
    for sentence in sentences[:max_sentences]:
        if total + len(sentence) > max_chars and kept:
            break
        kept.append(sentence)
        total += len(sentence) + 1

    if not kept:
        kept = [sentences[0][:max_chars]]

    result = " ".join(kept)
    if len(sentences) > len(kept):
        result = result.rstrip(".,!?।") + "."
    return result


def format_for_tts_segments(text: str) -> str:
    """Join sentences with newlines for providers that split on newlines."""
    return "\n".join(split_sentences(text))
