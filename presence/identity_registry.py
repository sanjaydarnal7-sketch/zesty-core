"""
Identity registry — known persons, biometric refs, links to Saved Profiles & Chief.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from presence.models import BiometricRefs, IdentityRole, PersonIdentity, PrivacyTier


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "unknown").lower()).strip("-")
    return slug or "unknown"


def _name_key(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


class IdentityRegistry:
    """File-backed store of enrolled identities."""

    def __init__(self, storage_path: str | Path | None = None) -> None:
        self.storage_path = Path(storage_path or "data/identity/registry.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._identities: dict[str, PersonIdentity] = {}
        self._by_profile_id: dict[str, str] = {}
        self._by_name: dict[str, str] = {}
        self.load()

    def _rebuild_indexes(self) -> None:
        self._by_profile_id = {}
        self._by_name = {}
        for ident in self._identities.values():
            self._index_identity(ident)

    def _index_identity(self, ident: PersonIdentity) -> None:
        if ident.saved_profile_id:
            self._by_profile_id[ident.saved_profile_id] = ident.identity_id
        key = _name_key(ident.display_name)
        if key:
            self._by_name[key] = ident.identity_id
        for alias in ident.aliases:
            alias_key = _name_key(alias)
            if alias_key:
                self._by_name[alias_key] = ident.identity_id

    def load(self) -> None:
        if not self.storage_path.is_file():
            self._identities = {}
            self._rebuild_indexes()
            return
        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
            records = raw.get("identities") or []
            self._identities = {
                rec["identity_id"]: PersonIdentity.from_dict(rec)
                for rec in records
                if rec.get("identity_id")
            }
            self._rebuild_indexes()
        except (json.JSONDecodeError, OSError, KeyError):
            self._identities = {}
            self._rebuild_indexes()

    def save(self) -> None:
        payload = {
            "version": 1,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "identities": [ident.to_dict() for ident in self._identities.values()],
        }
        self.storage_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_identities(self) -> list[PersonIdentity]:
        return list(self._identities.values())

    def get(self, identity_id: str) -> PersonIdentity | None:
        return self._identities.get(identity_id)

    def get_chief(self) -> PersonIdentity | None:
        for ident in self._identities.values():
            if ident.role == IdentityRole.CHIEF:
                return ident
        return None

    def ensure_chief(self, *, display_name: str = "Sanjay Darnal") -> PersonIdentity:
        chief = self.get_chief()
        if chief:
            return chief
        chief = PersonIdentity(
            identity_id="chief",
            display_name=display_name,
            role=IdentityRole.CHIEF,
            privacy_tier=PrivacyTier.FULL,
            owner_profile_ref="chief",
            aliases=["chief", "boss", "sanjay darnal", "sanjay"],
            enrolled_at=datetime.now().isoformat(timespec="seconds"),
        )
        self._identities[chief.identity_id] = chief
        self.save()
        return chief

    def find_by_saved_profile_id(self, profile_id: str) -> PersonIdentity | None:
        identity_id = self._by_profile_id.get(profile_id or "")
        if identity_id:
            return self._identities.get(identity_id)
        return None

    def find_by_face_embedding_id(self, embedding_id: str) -> PersonIdentity | None:
        if not embedding_id:
            return None
        for ident in self._identities.values():
            if ident.biometrics.face_embedding_id == embedding_id:
                return ident
        return None

    def find_by_display_name(self, name: str) -> PersonIdentity | None:
        target = _name_key(name)
        if not target:
            return None
        identity_id = self._by_name.get(target)
        if identity_id:
            return self._identities.get(identity_id)
        for ident in self._identities.values():
            candidates = [ident.display_name] + ident.aliases
            for candidate in candidates:
                c = _name_key(candidate)
                if c and (target in c or c in target):
                    return ident
        return None

    def link_saved_profile(self, identity_id: str, saved_profile_id: str) -> bool:
        ident = self._identities.get(identity_id)
        if not ident or not saved_profile_id:
            return False
        old_profile_id = ident.saved_profile_id
        ident.saved_profile_id = saved_profile_id
        ident.last_seen_at = datetime.now().isoformat(timespec="seconds")
        if old_profile_id and old_profile_id in self._by_profile_id:
            del self._by_profile_id[old_profile_id]
        self._index_identity(ident)
        self.save()
        return True

    def introduce_person(
        self,
        display_name: str,
        *,
        saved_profile_id: str = "",
        biometrics: BiometricRefs | None = None,
        notes: str = "",
    ) -> tuple[PersonIdentity, bool]:
        """
        Chief introduces someone — create or update identity, link vault profile if given.

        Returns (identity, created_new).
        """
        clean_name = display_name.strip()
        existing = self.find_by_display_name(clean_name)
        if existing and existing.role != IdentityRole.CHIEF:
            if saved_profile_id and existing.saved_profile_id != saved_profile_id:
                self.link_saved_profile(existing.identity_id, saved_profile_id)
            elif saved_profile_id and not existing.saved_profile_id:
                self.link_saved_profile(existing.identity_id, saved_profile_id)
            existing.last_seen_at = datetime.now().isoformat(timespec="seconds")
            self.save()
            return existing, False

        identity_id = f"person_{_slugify(clean_name)}_{int(time.time())}"
        ident = PersonIdentity(
            identity_id=identity_id,
            display_name=clean_name,
            role=IdentityRole.KNOWN,
            privacy_tier=PrivacyTier.STANDARD,
            saved_profile_id=saved_profile_id,
            biometrics=biometrics or BiometricRefs(),
            notes=notes or "Introduced by Chief",
            enrolled_at=datetime.now().isoformat(timespec="seconds"),
            last_seen_at=datetime.now().isoformat(timespec="seconds"),
            aliases=[_name_key(clean_name)] if _name_key(clean_name) else [],
        )
        self._identities[identity_id] = ident
        self._index_identity(ident)
        self.save()
        return ident, True

    def onboard_unknown(
        self,
        display_name: str,
        *,
        saved_profile_id: str = "",
        biometrics: BiometricRefs | None = None,
        notes: str = "",
    ) -> PersonIdentity:
        """Chief-approved onboarding of a previously unknown person."""
        ident, _ = self.introduce_person(
            display_name,
            saved_profile_id=saved_profile_id,
            biometrics=biometrics,
            notes=notes or "Onboarded by Chief",
        )
        return ident

    def touch_seen(self, identity_id: str, *, match_confidence: float = 0.0, persist: bool = False) -> None:
        ident = self._identities.get(identity_id)
        if not ident:
            return
        ident.last_seen_at = datetime.now().isoformat(timespec="seconds")
        if match_confidence:
            ident.biometrics.last_match_confidence = match_confidence
        if persist:
            self.save()

    def update_biometrics(self, identity_id: str, biometrics: BiometricRefs) -> bool:
        ident = self._identities.get(identity_id)
        if not ident:
            return False
        ident.biometrics = biometrics
        self.save()
        return True
