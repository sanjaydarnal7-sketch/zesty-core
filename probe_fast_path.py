"""Fast-path helpers for social / Deep Probe turns."""

from __future__ import annotations

import re
from typing import Any

_PURE_DATA_SIGNALS = (
    "search",
    "find",
    "latest",
    "everything you find",
    "everything you can find",
    "show me",
    "tell me everything",
    "instagram",
    "linkedin",
    "social profile",
    "social media",
    "profile",
    "picture",
    "photo",
    "web search",
    "bring my",
    "get the picture",
    "updated data",
)

_CONVERSATIONAL_SIGNALS = (
    "why ",
    "how should",
    "what do you think",
    "your opinion",
    "compare ",
    "explain in detail",
    "help me write",
    "draft ",
    "brainstorm",
    "disagree",
)


def is_pure_data_probe_query(text: str) -> bool:
    """True when probe data alone is enough — skip LLM rewrite."""
    lower = (text or "").lower()
    if not lower.strip():
        return False
    if any(sig in lower for sig in _CONVERSATIONAL_SIGNALS):
        return False
    return any(sig in lower for sig in _PURE_DATA_SIGNALS)


def format_probe_voice_summary(payload: dict[str, Any], *, owner_self: bool = False) -> str:
    """Short on-screen + voice summary; full detail stays in panel_text."""
    name = (payload.get("name") or "Subject").strip()
    if owner_self:
        return (
            "Chief — your profile data is on the Social panel, "
            "including photo and links when available."
        )

    platform = payload.get("platform") or "web"
    username = payload.get("username") or ""
    lines = [f"**{name}** — latest {platform} scan"]
    if username:
        lines[0] += f" (@{username.lstrip('@')})"

    counts: list[str] = []
    for key, label in (("followers", "followers"), ("following", "following"), ("connections", "connections")):
        val = payload.get(key)
        if val:
            counts.append(f"{val} {label}")
    if counts:
        lines.append(" · ".join(counts))

    findings = payload.get("key_findings") or []
    for item in findings[:4]:
        snippet = str(item).strip()
        if snippet:
            lines.append(f"- {snippet[:140]}")

    if len(lines) <= 1:
        panel = (payload.get("panel_text") or payload.get("facts_text") or "").strip()
        if panel:
            first_block = panel.split("\n\n")[0][:400]
            lines.append(first_block)

    return "\n".join(lines)
