"""
Chief / Owner identity for Zesty OS.

Biographical facts and roles live here — relationship tone stays in soul/injection.md.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DEFAULT_OWNER_PATH = Path(__file__).resolve().parent / "data" / "owner_profile.json"

_SELF_QUERY_PATTERNS = (
    r"\babout me\b",
    r"\babout myself\b",
    r"\bwho am i\b",
    r"\btell me about me\b",
    r"\bmy profile\b",
    r"\bmera profile\b",
    r"\bmeri profile\b",
    r"\bmera data\b",
    r"\bmeri jankari\b",
    r"\bmeri jaankari\b",
    r"\bmain kaun\b",
    r"\bwho is me\b",
    r"\beverything you can find about me\b",
    r"\bwhat do you know about me\b",
    r"\b(latest|updated)\s+data\b.*\b(me|my|instagram|profile)\b",
    r"\b(my|meri)\s+(instagram|photo|picture|profile pic|profile picture)\b",
    r"\b(get|bring)\s+(my|the)\s+(picture|photo|image)\b",
)

_CHIEF_REFERENCE_PATTERNS = (
    r"\bchief\b",
    r"\bmy chief\b",
    r"\bthe owner\b",
    r"\bzesty(?:'s)? owner\b",
    r"\bwho created zesty\b",
    r"\bwho made zesty\b",
    r"\bsanjay darnal\b",
    r"\bsanjay boss\b",
)


class OwnerProfile:
    """Loads and formats Chief/Owner identity for prompt injection."""

    def __init__(self, profile_path: str | Path | None = None) -> None:
        self.profile_path = Path(profile_path) if profile_path else DEFAULT_OWNER_PATH
        self._cache: dict[str, Any] | None = None

    def load(self, *, reload: bool = False) -> dict[str, Any]:
        if self._cache is not None and not reload:
            return self._cache
        if not self.profile_path.is_file():
            self._cache = {}
            return self._cache
        self._cache = json.loads(self.profile_path.read_text(encoding="utf-8"))
        return self._cache

    def get_aliases(self) -> list[str]:
        profile = self.load()
        aliases = list(profile.get("aliases") or [])
        full_name = (profile.get("full_name") or "").strip().lower()
        if full_name:
            aliases.append(full_name)
        return [a.lower() for a in aliases if a]

    def is_self_query(self, text: str) -> bool:
        lowered = (text or "").lower()
        if any(re.search(p, lowered) for p in _SELF_QUERY_PATTERNS):
            return True
        if re.search(r"\bsearch\b.*\babout me\b", lowered):
            return True
        if re.search(r"\bfind\b.*\babout me\b", lowered):
            return True
        return False

    def is_chief_reference(self, text: str) -> bool:
        lowered = (text or "").lower()
        return any(re.search(p, lowered) for p in _CHIEF_REFERENCE_PATTERNS)

    def is_owner_name_query(self, name: str) -> bool:
        normalized = re.sub(r"\s+", " ", (name or "").strip().lower())
        if not normalized:
            return False
        profile = self.load()
        full_name = (profile.get("full_name") or "").lower()
        if normalized == full_name:
            return True
        return normalized in self.get_aliases()

    def should_inject(self, user_text: str = "") -> bool:
        """Inject Chief block on every turn — Jarvis always knows the Chief."""
        return bool(self.load())

    def format_chief_identity_block(
        self,
        *,
        ask_update: bool = False,
    ) -> str:
        profile = self.load()
        if not profile:
            return ""

        address = profile.get("preferred_address") or "Chief"
        full_name = profile.get("full_name") or "Sanjay Darnal"
        lines = [
            "## Chief / Owner Identity",
            "",
            f"The **{address}** and sole owner of this system is **{full_name}**.",
            "When referring to him in dialogue, use **Chief** (not Boss, Sir, or generic user).",
            profile.get("disambiguation", ""),
            "",
            f"**Location:** {profile.get('location', 'Goa, India')}",
            f"**Title:** {profile.get('title', '')}",
        ]

        roles = profile.get("roles") or []
        if roles:
            lines.append("**Roles:**")
            for role in roles:
                lines.append(f"- {role}")

        orgs = profile.get("organizations") or []
        if orgs:
            lines.append("**Organizations:**")
            for org in orgs:
                if isinstance(org, dict):
                    lines.append(
                        f"- {org.get('name', '')} — {org.get('role', '')}: {org.get('focus', '')}"
                    )

        expertise = profile.get("expertise") or []
        if expertise:
            lines.append("**Expertise:** " + "; ".join(expertise))

        bio = profile.get("bio") or ""
        if bio:
            lines.append(f"**Bio:** {bio}")

        social = profile.get("social") or {}
        if social:
            lines.append("**Known profiles:**")
            for platform, url in social.items():
                if url:
                    lines.append(f"- {platform}: {url}")

        lines.extend(
            [
                "",
                "Never treat another person named Sanjay Darnal from web search as the Chief.",
                "Relationship tone (partner-in-crime, loyal, direct) comes from injection.md — not this block.",
            ]
        )

        if ask_update:
            lines.extend(
                [
                    "",
                    "**Turn instruction:** The Chief is asking about himself. After answering from the facts above, "
                    "ask exactly once in natural Zesty voice: "
                    "\"Chief, this is your current data. Would you like me to update it with the latest information?\"",
                ]
            )

        return "\n".join(line for line in lines if line is not None)

    def resolve_profile_image(self, deep_probe_engine: Any | None = None) -> str | None:
        """Return stored or scraped profile image URL for Chief."""
        profile = self.load()
        stored = (profile.get("profile_image_url") or "").strip()
        if stored:
            return stored

        if deep_probe_engine is None:
            return None

        from deep_probe_engine import select_best_profile_image

        social = profile.get("social") or {}
        full_name = profile.get("full_name") or "Sanjay Darnal"
        candidates: list[dict[str, Any]] = []
        for url in social.values():
            if not url or not str(url).startswith("http"):
                continue
            try:
                page_candidates = deep_probe_engine._fetch_page_image_candidates(
                    str(url),
                    {"title": full_name, "snippet": profile.get("bio") or ""},
                )
                candidates.extend(page_candidates)
            except Exception:
                continue

        if not candidates:
            return None

        pick = select_best_profile_image(candidates, subject_name=full_name)
        return (pick.get("url") or "").strip() or None

    def to_social_payload(self, *, deep_probe_engine: Any | None = None) -> dict[str, Any]:
        """Format owner data like a Deep Probe payload for Social Panel."""
        profile = self.load()
        if not profile:
            return {}
        panel_text = self.format_chief_identity_block()
        panel_text = panel_text.replace("## Chief / Owner Identity\n\n", "CHIEF / OWNER IDENTITY\n\n")
        image_url = self.resolve_profile_image(deep_probe_engine)
        return {
            "name": profile.get("full_name"),
            "username": profile.get("chief_id"),
            "platform": "owner",
            "bio": profile.get("bio"),
            "profile_image_url": image_url,
            "profile_image_source": "owner" if image_url else "owner",
            "profile_image_confidence": "high" if image_url else "low",
            "key_findings": profile.get("roles") or [],
            "social_links": [
                {"platform": k, "url": v}
                for k, v in (profile.get("social") or {}).items()
                if v
            ],
            "panel_text": panel_text,
            "facts_text": panel_text,
            "_owner_profile_source": True,
        }

    def update_profile(self, patch: dict[str, Any]) -> dict[str, Any]:
        profile = self.load(reload=True)
        profile.update(patch)
        profile["last_updated"] = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        self.profile_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
        self._cache = profile
        return profile
