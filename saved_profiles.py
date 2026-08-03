"""
Saved Profiles — persistent Deep Probe results in ChromaDB.

Supports save, list, update, delete, and retrieval-before-probe for any person.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

_SAVE_PATTERNS = (
    r"\bsave this\b",
    r"\bsave this profile\b",
    r"\bsave this data\b",
    r"\bremember this person\b",
    r"\bprofile save\b",
    r"\bprofile ko save\b",
    r"\bis profile ko save\b",
    r"\bye save kar\b",
    r"\bisko save kar\b",
    r"\bremember this profile\b",
)

_LIST_PATTERNS = (
    r"\bhow many profiles\b",
    r"\bshow saved profiles\b",
    r"\blist saved profiles\b",
    r"\blist profiles\b",
    r"\bsaved profiles\b",
    r"\bprofiles save hain\b",
    r"\bkine profiles\b",
    r"\bkitne profiles\b",
    r"\bprofiles dikhao\b",
    r"\bsaved profiles dikhao\b",
)

_UPDATE_PATTERNS = (
    r"\bupdate (?:this |the )?profile\b",
    r"\brefresh (?:this |the )?profile\b",
    r"\bprofile update\b",
    r"\bprofile purana\b",
    r"\bprofile refresh\b",
    r"\bupdate kar\b",
    r"\bprofile update kar\b",
    r"\bprofile refresh kar\b",
)

_DELETE_PATTERNS = (
    r"\bdelete (?:this |the )?profile\b",
    r"\bremove (?:this |the )?profile\b",
    r"\bprofile delete\b",
    r"\bprofile hata\b",
    r"\bprofile hata do\b",
    r"\bprofile remove\b",
    r"\bdelete kar\b",
    r"\bprofile delete kar\b",
    r"\bisko delete kar\b",
    r"\bis ko delete kar\b",
)

_LOOKUP_PATTERNS = (
    r"\bis .+ profile saved\b",
    r".+ ka (?:profile )?data hai",
    r".+ ki profile hai kya",
    r"\bdo you have .+ profile\b",
    r"\bfind .+ in saved\b",
    r"\bprofile saved hai kya\b",
)

_OPEN_PROFILE_PATTERNS = (
    r"\bopen .+ profile\b",
    r"\bshow .+ profile\b",
    r"\bdisplay .+ profile\b",
    r"\b.+ profile dikhao\b",
    r"\b.+ ka profile dikhao\b",
)


@dataclass
class ProfileCommandResult:
    handled: bool
    voice_text: str = ""
    open_panel: str = "chat"
    deep_probe: dict[str, Any] | None = None
    social_profile: dict[str, Any] | None = None
    target_image_url: str | None = None
    saved_profiles_list: list[dict[str, Any]] = field(default_factory=list)
    ui_mode: str = ""
    vault_payload: dict[str, Any] | None = None
    lookup_name: str = ""
    lookup_found: bool = False
    selected_profile_id: str = ""
    profile_action: str = ""


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "unknown").lower()).strip("-")
    return slug or "unknown"


_NAME_TITLE_PREFIX = re.compile(
    r"^(?:(?:dr|mr|mrs|ms|miss|prof|professor|sir|dame|shri|smt)\.?\s+)+",
    re.IGNORECASE,
)

_PLATFORM_PROBE_HINTS = {
    "linkedin": "linkedin",
    "instagram": "instagram",
    "x": "x",
    "twitter": "x",
    "facebook": "facebook",
    "web": "",
}


def clean_display_name(name: str) -> str:
    """Strip honorifics/titles from a person's display name."""
    cleaned = re.sub(r"\s+", " ", (name or "").strip())
    while cleaned:
        stripped = _NAME_TITLE_PREFIX.sub("", cleaned, count=1).strip()
        if stripped == cleaned:
            break
        cleaned = stripped
    return cleaned


def normalize_name_key(name: str) -> str:
    return re.sub(r"\s+", " ", clean_display_name(name).lower()).strip()


def names_are_similar(left: str, right: str) -> bool:
    """True when two display names likely refer to the same person."""
    a = normalize_name_key(left)
    b = normalize_name_key(right)
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    overlap = tokens_a & tokens_b
    if len(overlap) >= 2:
        return True
    if overlap and a.split()[-1] == b.split()[-1]:
        return True
    return False


def _profile_summary_text(data: dict[str, Any]) -> str:
    parts = [
        data.get("name") or "",
        data.get("username") or "",
        data.get("platform") or "",
        data.get("bio") or "",
        " ".join(data.get("key_findings") or []),
    ]
    return " ".join(p for p in parts if p).strip()


class SavedProfilesStore:
    """Chroma-backed store for saved person profiles."""

    _LAST_PROBE_META_KEY = "last_deep_probe"

    def __init__(
        self,
        collection,
        owner_profile=None,
        storage_dir: str | Path | None = None,
        *,
        working_memory_engine=None,
        conversation_manager=None,
        session_probe_dir: str | Path | None = None,
    ) -> None:
        self.collection = collection
        self.owner_profile = owner_profile
        self.working_memory_engine = working_memory_engine
        self.conversation_manager = conversation_manager
        self.storage_dir = Path(storage_dir or "data/saved_profiles")
        self.session_probe_dir = Path(session_probe_dir or "data/session_probe_context")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.session_probe_dir.mkdir(parents=True, exist_ok=True)
        self._last_probe_by_session: dict[str, dict[str, Any]] = {}

    def _payload_path(self, profile_id: str) -> Path:
        return self.storage_dir / f"{profile_id}.json"

    def _write_payload(self, profile_id: str, record: dict[str, Any]) -> None:
        self._payload_path(profile_id).write_text(
            json.dumps(record, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _read_payload(self, profile_id: str) -> dict[str, Any] | None:
        path = self._payload_path(profile_id)
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def _delete_payload(self, profile_id: str) -> None:
        path = self._payload_path(profile_id)
        if path.is_file():
            path.unlink()

    def set_last_probe(self, session_id: str, payload: dict[str, Any] | None) -> None:
        if not session_id or not payload:
            return

        probe_payload = dict(payload)
        self._last_probe_by_session[session_id] = probe_payload
        self._write_session_probe_file(session_id, probe_payload)
        self._sync_probe_to_working_memory(session_id, probe_payload)

    def get_last_probe(self, session_id: str) -> dict[str, Any] | None:
        if not session_id:
            return None

        cached = self._last_probe_by_session.get(session_id)
        if cached:
            return dict(cached)

        if self.working_memory_engine:
            try:
                wm_probe = self.working_memory_engine.get_metadata(
                    session_id, self._LAST_PROBE_META_KEY
                )
                if wm_probe:
                    self._last_probe_by_session[session_id] = dict(wm_probe)
                    return dict(wm_probe)
            except Exception:
                pass

        file_probe = self._read_session_probe_file(session_id)
        if file_probe:
            self._last_probe_by_session[session_id] = file_probe
            return dict(file_probe)

        return None

    def _session_probe_path(self, session_id: str) -> Path:
        safe_id = re.sub(r"[^a-zA-Z0-9._-]+", "_", session_id).strip("_") or "default"
        return self.session_probe_dir / f"{safe_id}.json"

    def _write_session_probe_file(self, session_id: str, payload: dict[str, Any]) -> None:
        try:
            self._session_probe_path(session_id).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _read_session_probe_file(self, session_id: str) -> dict[str, Any] | None:
        path = self._session_probe_path(session_id)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, OSError):
            return None

    def _sync_probe_to_working_memory(self, session_id: str, payload: dict[str, Any]) -> None:
        name = (payload.get("name") or "").strip()

        if self.working_memory_engine:
            try:
                self.working_memory_engine.set_metadata(
                    session_id, self._LAST_PROBE_META_KEY, dict(payload)
                )
                state = self.working_memory_engine.ensure_session(session_id)
                if name:
                    state.current_topic = name
                state.current_mode = "social_probe"
                state.user_intent = "profile_research"
                state.touch()
            except Exception:
                pass

        if self.conversation_manager:
            try:
                self.conversation_manager.ensure_session(session_id)
                if name:
                    self.conversation_manager.update_task(session_id, f"Profile: {name}")
                    self.conversation_manager.update_topic_structured(session_id, name)
                    self.conversation_manager.set_active_topic(session_id, name)
            except Exception:
                pass

    def categorize_profile(self, record: dict[str, Any]) -> str:
        data = record.get("data") or {}
        blob = " ".join(
            [
                str(record.get("name") or ""),
                str(data.get("bio") or ""),
                str(data.get("platform") or ""),
                " ".join(data.get("key_findings") or []),
            ]
        ).lower()
        if any(w in blob for w in ("mixologist", "bar", "hotel", "hospitality", "restaurant", "lounge", "chef", "beverage")):
            return "Hospitality"
        if any(w in blob for w in ("engineer", "developer", "tech", "software", "ai", "startup", "cto")):
            return "Tech"
        if any(w in blob for w in ("instagram", "creator", "influencer", "youtube", "artist", "content")):
            return "Creators"
        return "Personal"

    def profile_record_to_card(self, record: dict[str, Any]) -> dict[str, Any]:
        data = record.get("data") or {}
        return {
            "profile_id": record.get("profile_id"),
            "name": record.get("name"),
            "username": record.get("username") or data.get("username"),
            "platform": record.get("platform") or data.get("platform") or "web",
            "category": self.categorize_profile(record),
            "image_url": data.get("profile_image_url"),
            "bio": (data.get("bio") or "")[:140],
            "updated_at": (record.get("updated_at") or "")[:10],
            "data": data,
        }

    def build_vault_payload(self, profiles: list[dict[str, Any]]) -> dict[str, Any]:
        cards = [self.profile_record_to_card(p) for p in profiles]
        folders: dict[str, list[dict[str, Any]]] = {}
        for card in cards:
            cat = card.get("category") or "Personal"
            folders.setdefault(cat, []).append(card)
        return {
            "total": len(cards),
            "profiles": cards,
            "folders": folders,
        }

    def extract_lookup_name(self, text: str) -> str:
        patterns = (
            r"is (.+?)(?:'s|s)? profile saved",
            r"(.+?)(?:'s|s)? ka (?:profile )?data hai",
            r"(.+?)(?:'s|s)? ki profile hai kya",
            r"do you have (.+?)(?:'s|s)? profile",
            r"find (.+?) in saved",
            r"open (.+?) profile",
            r"show (.+?) profile",
            r"(.+?) profile dikhao",
            r"(.+?) ka profile dikhao",
        )
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip(" .,!?\"'")
                for noise in ("the", "this", "saved", "please", "kya", "mujhe"):
                    if name.lower().startswith(noise + " "):
                        name = name[len(noise) :].strip()
                if name and name.lower() not in ("this", "the", "profile", "saved"):
                    return name
        return ""

    def get_profile_by_id(self, profile_id: str) -> dict[str, Any] | None:
        record = self._read_payload(profile_id)
        return record

    def open_profile_record(self, name_or_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        record = None
        if name_or_id.startswith("profile_"):
            record = self._read_payload(name_or_id)
        if not record:
            record = self.find_by_name(name_or_id)
        if not record:
            return None, None
        data = record.get("data") or {}
        data["_saved_profile_source"] = True
        social = self.profile_to_social_payload(data)
        return record, social

    def _is_owner_profile(self, name: str) -> bool:
        if not self.owner_profile:
            return False
        return self.owner_profile.is_owner_name_query(name)

    def find_existing_profile(self, profile_data: dict[str, Any]) -> dict[str, Any] | None:
        """Return an existing saved record for the same person, if any."""
        name = (profile_data.get("name") or "").strip()
        username = (profile_data.get("username") or "").strip().lstrip("@").lower()

        for profile in self.list_profiles():
            data = profile.get("data") or {}
            existing_name = (profile.get("name") or data.get("name") or "").strip()
            if name and existing_name and names_are_similar(name, existing_name):
                return profile

            existing_user = (profile.get("username") or data.get("username") or "").strip().lstrip("@").lower()
            if username and existing_user and username == existing_user:
                return profile

        return None

    def build_refresh_probe_queries(
        self,
        name: str,
        record: dict[str, Any] | None = None,
    ) -> list[str]:
        """Build ordered probe queries — username/platform first, then cleaned name."""
        data = (record or {}).get("data") or {}
        username = (data.get("username") or (record or {}).get("username") or "").strip().lstrip("@")
        platform = (data.get("platform") or (record or {}).get("platform") or "").strip().lower()
        cleaned = clean_display_name(name)
        platform_hint = _PLATFORM_PROBE_HINTS.get(platform, platform)

        queries: list[str] = []
        seen: set[str] = set()

        def add(query: str) -> None:
            q = re.sub(r"\s+", " ", (query or "").strip())
            key = q.lower()
            if q and key not in seen:
                seen.add(key)
                queries.append(q)

        if username and platform_hint:
            add(f"search {username} {platform_hint}")
            add(f"find on {platform_hint} {username}")

        if cleaned:
            if platform_hint:
                add(f"search {cleaned} {platform_hint}")
            add(f"search {cleaned} linkedin")
            add(f"who is {cleaned}")

        if name and normalize_name_key(name) != normalize_name_key(cleaned):
            if platform_hint:
                add(f"search {cleaned} {platform_hint} profile")

        return queries

    def probe_for_refresh(
        self,
        deep_probe_engine,
        name: str,
        record: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Try multiple probe queries until fresh data is found."""
        if not deep_probe_engine:
            return None
        for query in self.build_refresh_probe_queries(name, record):
            fresh = deep_probe_engine.probe(query)
            if fresh:
                return fresh
        return None

    def _persist_profile(self, profile_id: str, record: dict[str, Any]) -> bool:
        profile_data = record.get("data") or {}
        name = record.get("name") or profile_data.get("name") or ""
        summary = _profile_summary_text(profile_data) or name
        updated_at = record.get("updated_at") or datetime.now().isoformat(timespec="seconds")
        source = record.get("source") or "deep_probe"
        try:
            self.collection.upsert(
                ids=[profile_id],
                documents=[summary],
                metadatas=[
                    {
                        "profile_id": profile_id,
                        "name": name,
                        "username": record.get("username") or profile_data.get("username") or "",
                        "platform": record.get("platform") or profile_data.get("platform") or "",
                        "updated_at": updated_at,
                        "source": source,
                    }
                ],
            )
            record["updated_at"] = updated_at
            self._write_payload(profile_id, record)
            return True
        except Exception:
            return False

    def save_profile(
        self,
        profile_data: dict[str, Any],
        *,
        source: str = "deep_probe",
    ) -> tuple[bool, str, str | None]:
        name = (profile_data.get("name") or "").strip()
        if not name:
            return False, "I need a name before I can save this profile.", None

        if self._is_owner_profile(name):
            return (
                False,
                "Chief, your identity is already locked in my Owner system — I don't save you as a generic profile.",
                None,
            )

        existing = self.find_existing_profile(profile_data)
        now = datetime.now().isoformat(timespec="seconds")

        if existing:
            profile_id = existing.get("profile_id")
            if not profile_id:
                return False, "That profile record looks corrupted — try saving it fresh.", None

            merged = {**(existing.get("data") or {}), **profile_data}
            merged["name"] = profile_data.get("name") or existing.get("name")
            record = {
                **existing,
                "name": merged["name"],
                "username": profile_data.get("username") or existing.get("username"),
                "platform": profile_data.get("platform") or existing.get("platform"),
                "updated_at": now,
                "source": source,
                "data": merged,
            }
            if self._persist_profile(profile_id, record):
                return True, f"Updated existing profile for **{record['name']}** in memory.", profile_id
            return False, "Couldn't update that profile right now — try again in a moment.", None

        profile_id = f"profile_{_slugify(name)}_{int(time.time())}"
        record = {
            "profile_id": profile_id,
            "name": name,
            "username": profile_data.get("username"),
            "platform": profile_data.get("platform"),
            "saved_at": now,
            "updated_at": now,
            "source": source,
            "data": profile_data,
        }

        if self._persist_profile(profile_id, record):
            return True, f"Saved profile for **{name}** to memory.", profile_id
        return False, "Couldn't save that profile right now — try again in a moment.", None

    def list_profiles(self) -> list[dict[str, Any]]:
        try:
            result = self.collection.get(include=["metadatas"])
            profiles: list[dict[str, Any]] = []
            for meta in result.get("metadatas") or []:
                if not meta:
                    continue
                profile_id = meta.get("profile_id")
                if profile_id:
                    record = self._read_payload(profile_id)
                    if record:
                        profiles.append(record)
                        continue
                profiles.append(
                    {
                        "profile_id": meta.get("profile_id"),
                        "name": meta.get("name"),
                        "platform": meta.get("platform"),
                        "updated_at": meta.get("updated_at"),
                    }
                )
            profiles.sort(key=lambda p: p.get("updated_at") or "", reverse=True)
            return profiles
        except Exception:
            return []

    def find_match(self, query: str, *, max_distance: float = 0.55) -> dict[str, Any] | None:
        if not (query or "").strip():
            return None

        if self.owner_profile and self.owner_profile.is_self_query(query):
            return None

        try:
            results = self.collection.query(query_texts=[query], n_results=3)
            if not results or not results.get("metadatas"):
                return None

            metas = results["metadatas"][0]
            distances = (results.get("distances") or [[]])[0]
            for meta, dist in zip(metas, distances):
                if not meta:
                    continue
                if dist is not None and dist > max_distance:
                    continue
                profile_id = meta.get("profile_id")
                record = self._read_payload(profile_id) if profile_id else None
                if record and record.get("data"):
                    data = dict(record["data"])
                    data["_saved_profile_source"] = True
                    data["_match_distance"] = dist
                    return data
        except Exception:
            return None
        return None

    def find_by_name(self, name: str) -> dict[str, Any] | None:
        target = normalize_name_key(name)
        if not target:
            return None
        for profile in self.list_profiles():
            pname = normalize_name_key(profile.get("name") or "")
            if not pname:
                continue
            if pname == target or target in pname or pname in target:
                return profile
            if names_are_similar(name, profile.get("name") or ""):
                return profile
        return None

    def delete_profile(self, name_or_id: str) -> tuple[bool, str]:
        target = (name_or_id or "").strip()
        if not target:
            return False, "Tell me which profile to delete — name or saved profile."

        profiles = self.list_profiles()
        if not profiles:
            return False, "No saved profiles yet — nothing to delete."

        match_id = None
        match_name = None
        lowered = target.lower()
        for profile in profiles:
            pid = profile.get("profile_id") or ""
            pname = (profile.get("name") or "").lower()
            if lowered == pid.lower() or lowered == pname or lowered in pname:
                match_id = pid
                match_name = profile.get("name")
                break

        if not match_id:
            return False, f"No saved profile matches \"{target}\". Say \"show saved profiles\" to see what's stored."

        try:
            self.collection.delete(ids=[match_id])
            self._delete_payload(match_id)
            return True, f"Deleted saved profile for **{match_name}**."
        except Exception:
            return False, "Couldn't delete that profile right now — try again."

    def update_profile(
        self,
        name_or_id: str,
        new_data: dict[str, Any],
    ) -> tuple[bool, str]:
        existing = self.find_by_name(name_or_id) or None
        if not existing:
            for profile in self.list_profiles():
                if (profile.get("profile_id") or "").lower() == name_or_id.lower():
                    existing = profile
                    break

        if not existing:
            return False, f"No saved profile found for \"{name_or_id}\". Say \"show saved profiles\" to check what's stored."

        profile_id = existing.get("profile_id")
        if not profile_id:
            return False, "That profile record looks corrupted — try saving it fresh."

        merged = {**(existing.get("data") or {}), **new_data}
        merged["name"] = new_data.get("name") or existing.get("name")
        merged["_saved_profile_source"] = True
        merged["_updated_from"] = "deep_probe_refresh"

        now = datetime.now().isoformat(timespec="seconds")
        record = {
            **existing,
            "name": merged["name"],
            "username": new_data.get("username") or existing.get("username"),
            "platform": new_data.get("platform") or existing.get("platform"),
            "updated_at": now,
            "source": "deep_probe_refresh",
            "data": merged,
        }

        if self._persist_profile(profile_id, record):
            return True, f"Updated saved profile for **{merged.get('name')}** with fresh data."
        return False, "Couldn't update that profile right now — try again in a moment."

    def format_list_overview(self, profiles: list[dict[str, Any]]) -> str:
        if not profiles:
            return "No saved profiles yet. Run a Deep Probe on someone, then say \"save this profile\"."

        lines = [f"SAVED PROFILES ({len(profiles)} total)", ""]
        for index, profile in enumerate(profiles, 1):
            name = profile.get("name") or "Unknown"
            platform = profile.get("platform") or profile.get("data", {}).get("platform") or "—"
            updated = (profile.get("updated_at") or "")[:10]
            lines.append(f"{index}. {name} — {platform} (updated {updated})")
        lines.append("")
        lines.append("Say a name to open one in detail, or \"delete profile for <name>\" to remove.")
        return "\n".join(lines)

    def profile_to_social_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        panel_text = data.get("panel_text") or ""
        if data.get("_owner_profile_source"):
            prefix = "[CHIEF / OWNER IDENTITY — not web search]\n\n"
            panel_text = prefix + panel_text if prefix.strip() not in panel_text else panel_text
        elif data.get("_saved_profile_source"):
            panel_text = "[SAVED PROFILE — from memory, not live search]\n\n" + panel_text
        return {
            "name": data.get("name"),
            "username": data.get("username"),
            "platform": data.get("platform"),
            "bio": data.get("bio"),
            "followers": data.get("followers"),
            "following": data.get("following"),
            "connections": data.get("connections"),
            "follower_delta": data.get("follower_delta"),
            "engagement_rate": data.get("engagement_rate"),
            "profile_image_url": data.get("profile_image_url"),
            "profile_image_source": data.get("profile_image_source"),
            "profile_image_confidence": data.get("profile_image_confidence"),
            "recent_activity": data.get("recent_activity"),
            "social_links": data.get("social_links"),
            "key_findings": data.get("key_findings"),
            "sources": data.get("sources"),
            "timeline": data.get("timeline"),
            "panel_text": panel_text,
            "saved_profile": True,
        }

    def parse_command(self, text: str) -> str | None:
        lowered = (text or "").lower()
        if any(re.search(p, lowered) for p in _SAVE_PATTERNS):
            return "save"
        if any(re.search(p, lowered) for p in _LIST_PATTERNS):
            return "list"
        if any(re.search(p, lowered) for p in _OPEN_PROFILE_PATTERNS):
            return "open"
        if any(re.search(p, lowered) for p in _LOOKUP_PATTERNS):
            return "lookup"
        if any(re.search(p, lowered) for p in _UPDATE_PATTERNS):
            return "update"
        if any(re.search(p, lowered) for p in _DELETE_PATTERNS):
            return "delete"
        return None

    def _extract_name_from_command(self, text: str) -> str:
        patterns = (
            r"(?:delete|remove|update|refresh)\s+(?:profile\s+)?(?:for\s+)?(.+?)(?:\s+profile)?$",
            r"profile\s+(?:for\s+)?(.+?)\s+(?:delete|hata|remove|update)",
        )
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip(" .,!?")
                for noise in ("this", "the", "isko", "is", "ye", "yeh"):
                    if name.lower().startswith(noise + " "):
                        name = name[len(noise) :].strip()
                if name and name.lower() not in ("this", "the", "profile"):
                    return name
        return ""

    def handle_command(
        self,
        text: str,
        session_id: str,
        *,
        deep_probe_engine=None,
    ) -> ProfileCommandResult:
        command = self.parse_command(text)
        if not command:
            return ProfileCommandResult(handled=False)

        if command == "save":
            last = self.get_last_probe(session_id)
            if not last:
                return ProfileCommandResult(
                    handled=True,
                    voice_text=(
                        "Nothing to save yet — search or probe someone first, "
                        "then say \"save this profile\"."
                    ),
                )
            ok, msg, profile_id = self.save_profile(last)
            profiles = self.list_profiles()
            return ProfileCommandResult(
                handled=True,
                voice_text=msg,
                open_panel="panelSocial" if ok else "chat",
                ui_mode="vault" if ok else "",
                vault_payload=self.build_vault_payload(profiles) if ok else None,
                saved_profiles_list=profiles if ok else [],
                selected_profile_id=profile_id or "",
                profile_action="save" if ok else "",
            )

        if command == "list":
            profiles = self.list_profiles()
            vault = self.build_vault_payload(profiles)
            voice = (
                f"Vault online — {len(profiles)} saved profile{'s' if len(profiles) != 1 else ''} indexed."
                if profiles
                else "Vault is empty — probe someone and say save this profile."
            )
            return ProfileCommandResult(
                handled=True,
                voice_text=voice,
                open_panel="panelSocial",
                ui_mode="vault",
                vault_payload=vault,
                saved_profiles_list=profiles,
            )

        if command == "lookup":
            name = self.extract_lookup_name(text)
            found = self.find_by_name(name) if name else None
            profiles = self.list_profiles()
            vault = self.build_vault_payload(profiles)
            if found:
                voice = f"Affirmative, Chief — {found.get('name')} is in the vault. Pulling their folder forward."
            elif name:
                voice = f"No saved profile for {name}. The vault scan came up empty."
            else:
                voice = "Tell me whose profile to search for in the vault."
            return ProfileCommandResult(
                handled=True,
                voice_text=voice,
                open_panel="panelSocial",
                ui_mode="vault_search",
                lookup_name=name,
                lookup_found=bool(found),
                vault_payload=vault,
                saved_profiles_list=profiles,
                selected_profile_id=(found or {}).get("profile_id", ""),
            )

        if command == "open":
            name = self.extract_lookup_name(text)
            record, social = self.open_profile_record(name)
            if not record:
                return ProfileCommandResult(
                    handled=True,
                    voice_text=f"No saved profile found for \"{name}\".",
                    open_panel="panelSocial",
                    ui_mode="vault_search",
                    lookup_name=name,
                    lookup_found=False,
                    vault_payload=self.build_vault_payload(self.list_profiles()),
                )
            data = record.get("data") or {}
            self.set_last_probe(session_id, data)
            return ProfileCommandResult(
                handled=True,
                voice_text=f"Opening {record.get('name')} — saved profile loaded from vault.",
                open_panel="panelSocial",
                ui_mode="profile_detail",
                deep_probe=data,
                social_profile=social,
                target_image_url=data.get("profile_image_url"),
                selected_profile_id=record.get("profile_id", ""),
                vault_payload=self.build_vault_payload(self.list_profiles()),
            )

        if command == "delete":
            name = self._extract_name_from_command(text) or self.extract_lookup_name(text)
            if not name:
                last = self.get_last_probe(session_id)
                name = (last or {}).get("name") or ""
            record = self.find_by_name(name) if name else None
            ok, msg = self.delete_profile(name)
            profiles = self.list_profiles()
            return ProfileCommandResult(
                handled=True,
                voice_text=msg,
                open_panel="panelSocial",
                ui_mode="vault" if ok else "chat",
                profile_action="delete" if ok else "",
                selected_profile_id=(record or {}).get("profile_id", ""),
                vault_payload=self.build_vault_payload(profiles),
                saved_profiles_list=profiles,
            )

        if command == "update":
            name = self._extract_name_from_command(text)
            if not name:
                last = self.get_last_probe(session_id)
                name = (last or {}).get("name") or ""
            if not name:
                return ProfileCommandResult(
                    handled=True,
                    voice_text="Which profile should I update? Give me the name or probe them first.",
                )
            if not deep_probe_engine:
                return ProfileCommandResult(
                    handled=True,
                    voice_text="Deep Probe engine isn't available — can't refresh that profile right now.",
                )
            record = self.find_by_name(name)
            fresh = self.probe_for_refresh(deep_probe_engine, name, record)
            if not fresh:
                return ProfileCommandResult(
                    handled=True,
                    voice_text=f"Couldn't find fresh data for **{name}** — profile not updated.",
                )
            ok, msg = self.update_profile(name, fresh)
            if ok:
                self.set_last_probe(session_id, fresh)
            social = self.profile_to_social_payload(fresh) if ok else None
            profiles = self.list_profiles()
            record = self.find_by_name(name)
            return ProfileCommandResult(
                handled=True,
                voice_text=msg,
                open_panel="panelSocial" if ok else "chat",
                ui_mode="profile_detail" if ok else "vault",
                profile_action="update" if ok else "",
                deep_probe=fresh if ok else None,
                social_profile=social,
                target_image_url=fresh.get("profile_image_url") if ok else None,
                selected_profile_id=(record or {}).get("profile_id", ""),
                vault_payload=self.build_vault_payload(profiles),
                saved_profiles_list=profiles,
            )

        return ProfileCommandResult(handled=False)
