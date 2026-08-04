"""
Fast Identity ↔ Saved Profile resolution.

O(1) profile_id lookups via registry index + in-memory profile cache.
No Chroma queries on the hot path.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from presence.models import PersonIdentity

if TYPE_CHECKING:
    from presence.identity_registry import IdentityRegistry
    from saved_profiles import SavedProfilesStore


class IdentityProfileBridge:
    """Resolves identity records to saved vault data with minimal I/O."""

    def __init__(
        self,
        registry: "IdentityRegistry",
        saved_profiles_store: "SavedProfilesStore | None" = None,
    ) -> None:
        self.registry = registry
        self.saved_profiles = saved_profiles_store
        self._profile_cache: dict[str, dict[str, Any]] = {}

    def get_profile_for_identity(self, identity: PersonIdentity | None) -> dict[str, Any] | None:
        if not identity or not identity.saved_profile_id:
            return None
        return self._load_by_id(identity.saved_profile_id)

    def get_profile_for_identity_id(self, identity_id: str) -> dict[str, Any] | None:
        ident = self.registry.get(identity_id)
        return self.get_profile_for_identity(ident)

    def find_profile_for_name(self, name: str) -> tuple[str, dict[str, Any] | None]:
        """Name → (profile_id, data). Uses saved_profiles.find_by_name (onboarding only)."""
        if not self.saved_profiles or not (name or "").strip():
            return "", None
        record = self.saved_profiles.find_by_name(name)
        if not record:
            return "", None
        profile_id = str(record.get("profile_id") or "")
        data = dict(record.get("data") or record)
        if profile_id:
            self._profile_cache[profile_id] = data
        return profile_id, data

    def _load_by_id(self, profile_id: str) -> dict[str, Any] | None:
        if not profile_id:
            return None
        if profile_id in self._profile_cache:
            return self._profile_cache[profile_id]
        if not self.saved_profiles:
            return None
        record = self.saved_profiles.get_profile_by_id(profile_id)
        if not record:
            return None
        data = dict(record.get("data") or record)
        self._profile_cache[profile_id] = data
        return data

    def format_brief(self, profile_data: dict[str, Any] | None) -> str:
        if not profile_data:
            return ""
        name = (profile_data.get("name") or "Unknown").strip()
        platform = (profile_data.get("platform") or "").strip()
        username = (profile_data.get("username") or "").strip().lstrip("@")
        parts = [f"Vault profile: {name}"]
        if platform:
            parts.append(f"platform={platform}")
        if username:
            parts.append(f"@{username}")
        bio = (profile_data.get("bio") or "").strip()
        if bio:
            parts.append(f"bio: {bio[:90]}")
        return " | ".join(parts)

    def invalidate(self, profile_id: str = "") -> None:
        if profile_id:
            self._profile_cache.pop(profile_id, None)
        else:
            self._profile_cache.clear()
