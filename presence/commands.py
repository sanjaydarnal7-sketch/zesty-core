"""
Lightweight presence command parsers — simulate modes & Chief introductions.

Pure regex + dict dispatch; no I/O, safe for the main request path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class SimulateAction(str, Enum):
    WAKE = "wake"
    SLEEP = "sleep"
    CHIEF = "chief"
    KNOWN = "known"
    UNKNOWN = "unknown"
    PRIVACY_HOLD = "privacy_hold"
    RESET = "reset"
    STATUS = "status"


@dataclass(frozen=True)
class SimulateCommand:
    action: SimulateAction
    name: str = ""


@dataclass(frozen=True)
class IntroductionCommand:
    display_name: str


_SIMULATE_RE = re.compile(
    r"^\s*(?:simulate|presence)\s+"
    r"(wake|sleep|chief|unknown|reset|status|privacy(?:\s*hold)?|secondary|known)(?:\s+(.+))?\s*$",
    re.IGNORECASE,
)

_INTRO_PATTERNS = (
    re.compile(
        r"\b(?:this is|meet|introducing|introduce|onboard|ye hai|yeh hai|"
        r"he is|she is|he's|she's|his name is|her name is|name is)\s+"
        r"(.+?)(?:\.|,|!|\?|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:say hi to|welcome)\s+(.+?)(?:\.|,|!|\?|$)",
        re.IGNORECASE,
    ),
)

_NOISE_PREFIXES = (
    "the",
    "my friend",
    "our guest",
    "a friend",
    "friend",
)


def _clean_person_name(raw: str) -> str:
    name = re.sub(r"\s+", " ", (raw or "").strip(" .,!?\"'"))
    lowered = name.lower()
    for prefix in _NOISE_PREFIXES:
        if lowered.startswith(prefix + " "):
            name = name[len(prefix) :].strip()
            lowered = name.lower()
    if lowered in ("him", "her", "them", "this person", "guest"):
        return ""
    return name


def parse_simulate_command(text: str) -> SimulateCommand | None:
    if not text:
        return None
    match = _SIMULATE_RE.match(text.strip())
    if not match:
        return None
    verb = match.group(1).lower().replace(" ", "")
    name = _clean_person_name(match.group(2) or "")
    if verb in ("privacy", "privacyhold", "secondary"):
        return SimulateCommand(SimulateAction.PRIVACY_HOLD)
    if verb == "known" and not name:
        return None
    action_map = {
        "wake": SimulateAction.WAKE,
        "sleep": SimulateAction.SLEEP,
        "chief": SimulateAction.CHIEF,
        "known": SimulateAction.KNOWN,
        "unknown": SimulateAction.UNKNOWN,
        "reset": SimulateAction.RESET,
        "status": SimulateAction.STATUS,
    }
    action = action_map.get(verb)
    if not action:
        return None
    return SimulateCommand(action=action, name=name)


def parse_introduction(text: str) -> IntroductionCommand | None:
    if not text:
        return None
    lowered = text.lower()
    if any(
        kw in lowered
        for kw in ("simulate ", "presence wake", "presence chief", "presence sleep")
    ):
        return None
    for pattern in _INTRO_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        name = _clean_person_name(match.group(1))
        if name and len(name) >= 2:
            return IntroductionCommand(display_name=name)
    return None
