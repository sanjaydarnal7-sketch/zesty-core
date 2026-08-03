"""
OpenPersona Runtime Loader for Zesty

Official integration with OpenPersona persona framework.
Loads generated persona artifacts as the framework intended:

  - SKILL.md  -> agent-facing behavior spec (Soul/Body shell)
  - soul/*.md -> priority-ordered personality stack
  - references/*.md -> faculty modules declared in persona.json
  - persona.json -> persona declaration
  - scripts/state-sync.js -> Body nervous system (state read/write/signal)

Reference: OpenPersona Runner Integration Protocol
  https://github.com/acnlabs/OpenPersona#runner-integration-protocol
"""

from __future__ import annotations

import json
import re
import subprocess
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Personality-first order (injection is source of truth per SKILL.md)
_SOUL_PRIORITY_FILES = (
    "injection.md",
    "CONVERSATION_DNA.md",
    "behavior-guide.md",
    "constitution.md",
)

_FACULTY_REFERENCE_MAP = {
    "memory": "references/memory.md",
    "voice": "references/voice.md",
}

_SELF_NARRATIVE_TEMPLATE_MARKERS = (
    "_Written and maintained by",
    "Append new entries",
)


class OpenPersonaRuntimeError(Exception):
    """Raised when the OpenPersona runtime cannot be loaded or executed."""


@dataclass(frozen=True)
class PromptSections:
    """Decomposed system prompt for observability and budget trimming."""

    soul_stack: str
    faculty_block: str
    skill_shell: str
    identity_guards: str

    def assemble(self, *, include_faculties: bool = True) -> str:
        # Personality first. Faculties are optional how-to docs and dilute identity.
        parts = [self.soul_stack]
        parts.append(
            "## Authority\n\n"
            "The soul stack above is authoritative for identity, tone, language, and behavior. "
            "Everything below is supporting context only and must never override it."
        )
        if self.identity_guards.strip():
            parts.append(self.identity_guards)
        if self.skill_shell.strip():
            parts.append(self.skill_shell)
        if include_faculties and self.faculty_block.strip():
            parts.append(self.faculty_block)
        return "\n\n".join(p for p in parts if p.strip())


class OpenPersonaPersona:
    """
    Loads and represents an OpenPersona persona for use in a Python runtime.
    """

    def __init__(self, persona_dir: str | Path) -> None:
        self.persona_dir = Path(persona_dir).resolve()
        self._skill_md: str | None = None
        self._persona_json: dict | None = None
        self._prompt_sections: PromptSections | None = None
        self._state_sync_script: Path | None = None

        self._validate_pack()
        self._locate_artifacts()

    def _validate_pack(self) -> None:
        """Verify this directory contains a valid OpenPersona persona pack."""
        if not self.persona_dir.is_dir():
            raise OpenPersonaRuntimeError(
                f"Persona directory does not exist: {self.persona_dir}"
            )

        has_persona_json = (
            (self.persona_dir / "persona.json").is_file()
            or (self.persona_dir / "soul" / "persona.json").is_file()
        )
        has_skill_md = (
            (self.persona_dir / "SKILL.md").is_file()
            or (self.persona_dir / "SKILL" / "SKILL.md").is_file()
            or (self.persona_dir / "skill" / "SKILL.md").is_file()
        )

        if not has_persona_json and not has_skill_md:
            raise OpenPersonaRuntimeError(
                f"Not a valid OpenPersona pack: no persona.json or SKILL.md found in {self.persona_dir}"
            )

    def _locate_artifacts(self) -> None:
        """Locate the key runtime artifacts within the pack."""
        skill_md_candidates = [
            self.persona_dir / "SKILL.md",
            self.persona_dir / "SKILL" / "SKILL.md",
            self.persona_dir / "skill" / "SKILL.md",
        ]
        for candidate in skill_md_candidates:
            if candidate.is_file():
                self._skill_md_path = candidate
                break
        else:
            self._skill_md_path = None

        persona_json_candidates = [
            self.persona_dir / "persona.json",
            self.persona_dir / "soul" / "persona.json",
        ]
        for candidate in persona_json_candidates:
            if candidate.is_file():
                self._persona_json_path = candidate
                break
        else:
            self._persona_json_path = None

        self._state_sync_script = self.persona_dir / "scripts" / "state-sync.js"
        if not self._state_sync_script.is_file():
            self._state_sync_script = None

    @property
    def skill_md(self) -> str:
        """Return the raw SKILL.md content (agent-facing behavior spec)."""
        if self._skill_md is None:
            if self._skill_md_path is None:
                raise OpenPersonaRuntimeError("SKILL.md not found in persona pack")
            self._skill_md = self._skill_md_path.read_text(encoding="utf-8")
        return self._skill_md

    @property
    def persona_json(self) -> dict:
        """Return the parsed persona.json declaration."""
        if self._persona_json is None:
            if self._persona_json_path is None:
                raise OpenPersonaRuntimeError("persona.json not found in persona pack")
            raw = self._persona_json_path.read_text(encoding="utf-8")
            self._persona_json = json.loads(raw)
        return self._persona_json

    @property
    def persona_root(self) -> Path:
        """Return the persona root directory (pack root or soul/ parent)."""
        if self._persona_json_path is None:
            return self.persona_dir
        if self._persona_json_path.parent.name == "soul":
            return self._persona_json_path.parent.parent
        return self.persona_dir

    def _read_soul_file(self, filename: str) -> str | None:
        """Read a file from the soul/ directory, returning None if absent."""
        candidates = [
            self.persona_root / "soul" / filename,
            self.persona_dir / "soul" / filename,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate.read_text(encoding="utf-8")
        return None

    def _read_pack_file(self, relative_path: str) -> str | None:
        """Read a file relative to the persona pack root."""
        candidates = [
            self.persona_root / relative_path,
            self.persona_dir / relative_path,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate.read_text(encoding="utf-8")
        return None

    @staticmethod
    def _normalize_soul_text(text: str) -> str:
        return text.strip()

    def _load_soul_content(self) -> str:
        """
        Concatenate soul files in personality-first order
        (injection.md → CONVERSATION_DNA.md → behavior-guide.md → constitution.md).
        """
        parts: list[str] = []
        for filename in _SOUL_PRIORITY_FILES:
            content = self._read_soul_file(filename)
            if content:
                parts.append(self._normalize_soul_text(content))

        narrative = self._load_self_narrative()
        if narrative:
            parts.append(narrative)

        return "\n\n".join(parts)

    def _load_self_narrative(self) -> str | None:
        """Include self-narrative only when it contains real entries, not just the template."""
        raw = self._read_soul_file("self-narrative.md")
        if not raw:
            return None

        lines = [
            line.strip()
            for line in raw.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        substantive = [
            line
            for line in lines
            if not any(marker in line for marker in _SELF_NARRATIVE_TEMPLATE_MARKERS)
        ]
        if not substantive:
            return None
        return self._normalize_soul_text(raw)

    def _load_faculty_references(self) -> str:
        """Inline faculty reference docs declared in persona.json."""
        faculties = self.persona_json.get("faculties", [])
        if not faculties:
            return ""

        parts: list[str] = []
        seen_paths: set[str] = set()

        for faculty in faculties:
            name = faculty.get("name") if isinstance(faculty, dict) else str(faculty)
            rel_path = _FACULTY_REFERENCE_MAP.get(name)
            if not rel_path or rel_path in seen_paths:
                continue
            seen_paths.add(rel_path)
            content = self._read_pack_file(rel_path)
            if content:
                parts.append(
                    f"## Faculty: {name.title()}\n\n{self._normalize_soul_text(content)}"
                )

        if not parts:
            return ""
        return "## Faculty References\n\n" + "\n\n".join(parts)

    def _strip_skill_md(self, raw: str) -> str:
        """
        Drop SKILL.md personality redefinitions (soul already loaded).
        Keep only a minimal non-personality runtime pointer.
        """
        prompt = re.sub(r"^---\s*\n.*?\n---\s*\n", "", raw, flags=re.DOTALL)
        for marker in (
            "\n## Generated Files",
            "\n## Faculty",
            "\n## Signal Protocol",
            "\n## Interface",
            "\n## Soul",
        ):
            prompt = prompt.split(marker, maxsplit=1)[0]
        # Body section alone is metadata — do not redefine personality.
        if "## Body" in prompt or prompt.strip().startswith("# Zesty"):
            return (
                "## Pack Pointer\n\n"
                "Identity/tone/language: soul/injection.md + soul/CONVERSATION_DNA.md. "
                "Do not invent a second personality."
            )
        return prompt.strip()

    def _build_identity_guards(self) -> str:
        return (
            "## Name Lock\n\n"
            "Your only name is Zesty. Never use George, Jestee, Hermes, or any other name.\n\n"
            "## Tool Honesty\n\n"
            "Never claim you searched or used tools unless host results appear below."
        )

    def get_prompt_sections(self) -> PromptSections:
        """Return decomposed prompt sections (cached)."""
        if self._prompt_sections is None:
            soul_stack = self._load_soul_content()
            if not soul_stack:
                raise OpenPersonaRuntimeError(
                    "Persona soul stack is empty — check soul/*.md files in the pack"
                )

            skill_shell = self._strip_skill_md(self.skill_md)

            self._prompt_sections = PromptSections(
                soul_stack=soul_stack,
                faculty_block=self._load_faculty_references(),
                skill_shell=skill_shell,
                identity_guards=self._build_identity_guards(),
            )
        return self._prompt_sections

    def invalidate_prompt_cache(self) -> None:
        """Drop cached prompt sections after pack edits."""
        self._prompt_sections = None
        self._skill_md = None

    def build_system_prompt(self, *, include_faculties: bool = True) -> str:
        """Assemble the static persona system prompt."""
        return self.get_prompt_sections().assemble(include_faculties=include_faculties)

    def get_system_prompt(self) -> str:
        """Backward-compatible alias for build_system_prompt()."""
        return self.build_system_prompt(include_faculties=True)

    @property
    def persona_name(self) -> str:
        """Human-readable persona name."""
        return self.persona_json.get("personaName") or self.persona_json.get(
            "soul", {}
        ).get("identity", {}).get("personaName", "Unknown")

    @property
    def slug(self) -> str:
        """Persona slug (directory-friendly identifier)."""
        return self.persona_json.get("slug") or self.persona_json.get(
            "soul", {}
        ).get("identity", {}).get("slug", "unknown")

    # ------------------------------------------------------------------
    # State management — delegates to OpenPersona's own state-sync.js
    # ------------------------------------------------------------------

    def _run_state_sync(self, *args: str) -> str:
        """Execute scripts/state-sync.js with the given arguments."""
        if self._state_sync_script is None:
            raise OpenPersonaRuntimeError(
                "scripts/state-sync.js not found — regenerate the persona pack with a current OpenPersona version"
            )

        cmd = ["node", str(self._state_sync_script)] + list(args)
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.persona_dir),
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except FileNotFoundError:
            raise OpenPersonaRuntimeError(
                "Node.js is not installed or not in PATH. "
                "OpenPersona state-sync.js requires Node.js >= 18."
            )
        except subprocess.TimeoutExpired:
            raise OpenPersonaRuntimeError("state-sync.js timed out after 30s")

        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise OpenPersonaRuntimeError(
                f"state-sync.js failed (exit {result.returncode}): {stderr}"
            )

        return result.stdout.strip()

    def read_state(self) -> dict:
        """Read the persona's current evolution state via state-sync.js."""
        output = self._run_state_sync("read")
        try:
            return json.loads(output) if output else {}
        except json.JSONDecodeError:
            logger.warning("state-sync read returned non-JSON output: %s", output[:200])
            return {}

    def write_state(self, patch: dict) -> None:
        """Merge a JSON patch into state.json via state-sync.js."""
        if not isinstance(patch, dict):
            raise OpenPersonaRuntimeError("state patch must be a JSON object")
        self._run_state_sync("write", json.dumps(patch))

    def signal(self, signal_type: str, payload: dict | None = None) -> None:
        """Emit a capability/resource signal to the host runtime."""
        if payload is None:
            self._run_state_sync("signal", signal_type)
        else:
            self._run_state_sync("signal", signal_type, json.dumps(payload))

    # ------------------------------------------------------------------
    # Conversation helpers
    # ------------------------------------------------------------------

    def build_conversation_context(self) -> dict:
        """
        Build runtime context from state.json for injection into the LLM prompt.
        """
        state = self.read_state()
        context_parts: list[str] = []

        mood = state.get("mood") or {}
        if mood:
            current = mood.get("current", "neutral")
            baseline = mood.get("baseline")
            intensity = mood.get("intensity")
            mood_line = f"[CURRENT MOOD: {current}"
            if baseline:
                mood_line += f", baseline: {baseline}"
            if intensity is not None:
                mood_line += f", intensity: {intensity}"
            mood_line += "]"
            context_parts.append(mood_line)

        relationship = state.get("relationship") or {}
        if relationship:
            stage = relationship.get("stage", "acquaintance")
            count = relationship.get("interactionCount")
            rel_line = f"[RELATIONSHIP STAGE: {stage}"
            if count is not None:
                rel_line += f", interactions: {count}"
            rel_line += "]"
            context_parts.append(rel_line)

        evolved = state.get("evolvedTraits") or state.get("traits") or []
        if evolved:
            context_parts.append(f"[EVOLVED TRAITS: {', '.join(map(str, evolved))}]")

        drift = state.get("speakingStyleDrift") or {}
        if drift:
            formality = drift.get("formality", 0)
            verbosity = drift.get("verbosity")
            emoji_freq = drift.get("emoji_frequency")
            drift_bits = [f"formality: {formality}"]
            if verbosity is not None:
                drift_bits.append(f"verbosity: {verbosity}")
            if emoji_freq is not None:
                drift_bits.append(f"emoji: {emoji_freq}")
            context_parts.append(f"[SPEAKING STYLE: {', '.join(drift_bits)}]")

        interests = state.get("interests")
        if interests:
            if isinstance(interests, dict) and interests:
                interest_str = ", ".join(f"{k}: {v}" for k, v in interests.items())
            elif isinstance(interests, list) and interests:
                interest_str = ", ".join(map(str, interests))
            else:
                interest_str = ""
            if interest_str:
                context_parts.append(f"[INTERESTS: {interest_str}]")

        # eventLog / recentEvents intentionally omitted from prompt injection:
        # free-text deltas contaminated personality (forced slang, wrong names, tone).
        # State management (read/write/persist) remains available separately.

        pending = state.get("pendingCommands") or []
        if pending:
            cmd_summaries = []
            for cmd in pending:
                if not isinstance(cmd, dict):
                    continue
                cmd_type = cmd.get("type", "unknown")
                payload = cmd.get("payload", {})
                cmd_summaries.append(f"{cmd_type}: {json.dumps(payload)}")
            if cmd_summaries:
                context_parts.append(
                    f"[PENDING HOST COMMANDS: {'; '.join(cmd_summaries)}]"
                )

        injection_text = "\n".join(context_parts)
        return {
            "raw_state": state,
            "injection_text": injection_text,
        }

    def format_runtime_context(self) -> str:
        """Return non-dialogue state.json modifiers for the system prompt."""
        ctx = self.build_conversation_context()
        injection = ctx.get("injection_text", "").strip()
        if not injection:
            return ""
        return (
            "## Runtime State\n\n"
            "Mood/relationship only. Must not change identity, tone, or language rules.\n\n"
            f"{injection}"
        )

    def persist_conversation_event(
        self,
        event_type: str,
        trigger: str,
        delta: str,
        source: str = "conversation",
    ) -> None:
        """Append a significant event to the persona's eventLog."""
        current_state = self.read_state()
        event_log = current_state.get("eventLog") or []
        event_log.append({
            "type": event_type,
            "trigger": trigger,
            "delta": delta,
            "source": source,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        })
        if len(event_log) > 50:
            event_log = event_log[-50:]

        current_state["eventLog"] = event_log
        current_state["pendingCommands"] = []
        self.write_state(current_state)
