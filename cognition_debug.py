"""Runtime cognition debug — observability only. No production behavior changes."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

DEBUG_COGNITION = os.environ.get("DEBUG_COGNITION", "false").lower() in ("true", "1", "yes")


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def infer_intent_label(execution_flags: dict[str, bool]) -> str:
    labels: list[str] = []
    if execution_flags.get("disagree"):
        labels.append("disagreement")
    if execution_flags.get("one_sentence"):
        labels.append("concise")
    if execution_flags.get("rewrite"):
        labels.append("rewrite")
    if execution_flags.get("one_action"):
        labels.append("action")
    return ", ".join(labels) if labels else "general"


def memory_reject_reason(text: str) -> str | None:
    """Mirror main._is_assistant_style_memory logic — labels only, no behavior change."""
    raw = (text or "").strip()
    if not raw:
        return "empty document"
    lower = raw.lower()
    if re.match(r"^(zesty|assistant|bot|ai|hermes|jestee|user)\s*:", raw, re.IGNORECASE):
        return "stored dialogue turn (role prefix)"
    if re.search(r"(^|\n)\s*(zesty|assistant|bot|ai|user)\s*:", raw, re.IGNORECASE):
        return "stored dialogue turn (embedded role prefix)"
    dialogue_markers = (
        ("how can i assist", "assistant service phrase"),
        ("how can i help", "assistant service phrase"),
        ("what can i help", "assistant service phrase"),
        ("i'd be happy to", "assistant service phrase"),
        ("i am happy to help", "assistant service phrase"),
        ("i'm happy to help", "assistant service phrase"),
        ("i remember you asking", "false memory / assistant phrase"),
        ("is there anything else", "assistant service phrase"),
        ("as an ai", "assistant identity phrase"),
        ("let me know if you need", "assistant service phrase"),
        ("how's that for a", "assistant template phrase"),
        ("thank you for sharing", "therapist phrase"),
        ("how does that make you feel", "therapist phrase"),
        ("i'm here for you", "therapist phrase"),
        ("good morning", "greeting template"),
        ("good afternoon", "greeting template"),
        ("good evening", "greeting template"),
        ("hey sanjay", "greeting template"),
        ("hello sanjay", "greeting template"),
    )
    for marker, reason in dialogue_markers:
        if marker in lower:
            return reason
    if re.search(r"\b(yaar|yar|यार)\b", lower):
        return "forbidden slang (yaar/yar)"
    if len(raw) > 400:
        return "overlong dialogue monologue"
    if re.match(r"^(hi|hello|hey|namaste)\b", lower) and ("?" in raw or "help" in lower):
        return "greeting / service template"
    return None


def audit_sanitize_changes(before: str, after: str) -> list[dict[str, str]]:
    """Read-only audit mirroring ZestyCommercialOS._sanitize_response removals."""
    if (before or "").strip() == (after or "").strip():
        return []

    changes: list[dict[str, str]] = []
    working = before or ""

    fragments: list[tuple[str, str]] = [
        ("It seems like we've just started our conversation,", "meta leak"),
        ("and I'm ready to chat with you.", "meta leak"),
        ("I've got my personality and conversation guidelines all set,", "meta leak"),
        ("so let's dive right in.", "meta leak"),
        ("Looks like we've got a lot of context and guidelines here.", "meta leak"),
        ("It seems like we're setting the stage for our conversations.", "meta leak"),
        ("I see we've got a pretty detailed framework for how we'll interact.", "meta leak"),
        ("We've got a set of rules and guidelines that help me understand how to interact with you", "meta leak"),
        ("rules and guidelines", "meta leak"),
        ("conversation guidelines", "meta leak"),
        ("playbook", "meta leak"),
        ("I'll break it down for you", "lecture phrase"),
        ("pretty detailed guide", "meta leak"),
        ("framework for how we'll interact", "meta leak"),
    ]
    for fragment, reason in fragments:
        if fragment in working:
            changes.append({"removed": fragment, "reason": reason})
            working = working.replace(fragment, "")

    style_res: list[tuple[str, str]] = [
        (r"how can i (help|assist)( you)?( today)?\??", "assistant phrase"),
        (r"what can i (do|help) (for|you)[^.!?]*[.!]?", "assistant phrase"),
        (r"i'?d be happy to (help|assist)[^.!?]*[.!]?", "assistant phrase"),
        (r"i('m| am) (here to help|happy to help|here for you)[^.!?]*[.!]?", "assistant phrase"),
        (r"is there anything else( i can (help|assist) you with)?\??", "assistant phrase"),
        (r"let me know if (you need|there'?s)[^.!?]*[.!]?", "assistant phrase"),
        (r"as an ai( assistant)?[^.!?]*[.!]?", "assistant identity phrase"),
        (r"i (hear you|understand how you feel)[^.!?]*[.!]?", "therapist phrase"),
        (r"thank you for sharing[^.!?]*[.!]?", "therapist phrase"),
        (r"how does that make you feel\??", "therapist phrase"),
        (r"\bmadam(\s*ji)?\b", "honorific polish"),
        (r"i hope (this helps|that helps)[^.!?]*[.!]?", "assistant phrase"),
        (r"feel free to (ask|reach out)[^.!?]*[.!]?", "assistant phrase"),
        (r"आइए\s+(पहले\s+)?(इस\s+)?(विषय|मुद्दे|बात)\s*(को\s*)?(समझते|देखते|चर्चा)\s*[^\n।.!?]*[।.!?]?", "Hindi lecturer opener"),
        (r"चलिए\s+(इस|हम)\s*[^\n।.!?]*?(चर्चा|विस्तार|समझ)[^\n।.!?]*[।.!?]?", "Hindi lecturer opener"),
        (r"मैं\s+आपकी\s+सहायता\s+कर\s+सकता\s+हूँ[^\n।.!?]*[।.!?]?", "Hindi assistant phrase"),
        (r"मैं\s+आपकी\s+मदद\s+के\s+लिए\s+(यहाँ\s+)?हूँ[^\n।.!?]*[।.!?]?", "Hindi assistant phrase"),
        (r"मैं\s+समझता\s+हूँ\s+कि\s+आपको\s+[^\n।.!?]*[।.!?]?", "Hindi therapist phrase"),
        (r"कृपया\s+(बता[^\n।.!?]*|मुझे\s+जानने)[^\n।.!?]*[।.!?]?", "Hindi formal phrase"),
        (r"आपकी\s+सेवा\s+में\s+[^\n।.!?]*[।.!?]?", "Hindi formal phrase"),
        (r"महोदय[^\n।.!?]*[।.!?]?", "Hindi formal phrase"),
        (r"Madam\s*ji", "honorific polish"),
        (r"मैं\s+आपको\s+समझाने\s+की\s+कोशिश[^\n।.!?]*[।.!?]?", "Hindi lecture phrase"),
        (r"इस\s+विषय\s+पर\s+विस्तार\s+से\s+[^\n।.!?]*[।.!?]?", "Hindi lecture phrase"),
        (r"\bwe (already|'ve already|had already) (discussed|talked about|resolved|solved|decided)[^.!?]*[.!?]?", "false shared-history claim"),
        (r"\bwe solved that[^.!?]*[.!?]?", "false shared-history claim"),
        (r"\byou told me (earlier|before)[^.!?]*[.!?]?", "false shared-history claim"),
        (r"\b(humne|hum) (pehle|already) (discuss|baat|resolve|solve|kar liya|kiya tha)[^.!?]*[.!?]?", "false shared-history claim"),
        (r"\b(humne|hum) usse resolve kar liya tha[^.!?]*[.!?]?", "false shared-history claim"),
        (r"\b(tumne|aapne) (pehle|पहले) (bataya|kaha|mentioned)[^.!?]*[.!?]?", "false shared-history claim"),
        (r"\bwe('ve| have) been putting off[^.!?]*[.!?]?", "false shared-history claim"),
        (r"मैं समझता हूँ कि हमने पहले[^।.!?]*[।.!?]?", "false shared-history claim"),
    ]
    for pattern, reason in style_res:
        match = re.search(pattern, working, flags=re.IGNORECASE)
        if match:
            changes.append({"removed": match.group(0).strip(), "reason": reason})

    if not changes and before.strip() != after.strip():
        changes.append(
            {
                "removed": f"(diff {len(before) - len(after)} chars)",
                "reason": "whitespace or punctuation normalization",
            }
        )
    return changes


def audit_enforce_changes(before: str, after: str, execution_flags: dict[str, bool]) -> list[dict[str, str]]:
    if (before or "").strip() == (after or "").strip():
        return []
    reasons: list[str] = []
    if execution_flags.get("one_sentence"):
        reasons.append("one_sentence flag")
    if execution_flags.get("one_action"):
        reasons.append("one_action flag")
    if not reasons:
        reasons.append("Hindi length cap or sentence trim")
    return [{"removed": f'"{before[:120]}"', "reason": " → ".join(reasons)}]


@dataclass
class CognitionDebugTrace:
    user_message: str = ""
    detected_language: str = ""
    session_language: str = ""
    detected_intent: str = ""
    execution_flags: dict[str, bool] = field(default_factory=dict)

    core_prompt_tokens: int = 0
    runtime_tokens: int = 0
    history_tokens: int = 0
    memory_tokens: int = 0
    total_tokens: int = 0

    raw_chroma: Any = None
    accepted_memories: list[dict[str, str]] = field(default_factory=list)
    rejected_memories: list[dict[str, str]] = field(default_factory=list)

    history_used: str = ""
    semantic_state: str = ""
    pending_tasks: list[str] = field(default_factory=list)
    current_topic: str = ""
    user_intent: str = ""

    provider: str = ""
    model: str = ""
    api_key_index: int | None = None
    temperature: float = 0.0

    raw_model_output: str = ""
    sanitize_changes: list[dict[str, str]] = field(default_factory=list)
    enforce_changes: list[dict[str, str]] = field(default_factory=list)
    final_output: str = ""

    def set_request(
        self,
        *,
        user_message: str,
        detected_language: str,
        session_language: str,
        execution_flags: dict[str, bool],
    ) -> None:
        self.user_message = user_message
        self.detected_language = detected_language
        self.session_language = session_language
        self.execution_flags = dict(execution_flags)
        self.detected_intent = infer_intent_label(execution_flags)

    def set_prompt_tokens(
        self,
        *,
        core_prompt: str,
        runtime_block: str,
        history_text: str,
        memory_text: str,
        user_message: str,
    ) -> None:
        self.core_prompt_tokens = _estimate_tokens(core_prompt)
        self.runtime_tokens = _estimate_tokens(runtime_block)
        self.history_tokens = _estimate_tokens(history_text)
        self.memory_tokens = _estimate_tokens(memory_text)
        self.total_tokens = _estimate_tokens(
            core_prompt + runtime_block + history_text + memory_text + user_message
        )

    def set_memory(
        self,
        *,
        raw_chroma: Any,
        accepted: list[dict[str, str]],
        rejected: list[dict[str, str]],
    ) -> None:
        self.raw_chroma = raw_chroma
        self.accepted_memories = accepted
        self.rejected_memories = rejected

    def set_continuity(
        self,
        *,
        history_used: str,
        semantic_state: str,
        pending_tasks: list[str],
        current_topic: str,
        user_intent: str,
    ) -> None:
        self.history_used = history_used
        self.semantic_state = semantic_state
        self.pending_tasks = list(pending_tasks)
        self.current_topic = current_topic or "(none)"
        self.user_intent = user_intent or "(none)"

    def set_model(
        self,
        *,
        provider: str,
        model: str,
        api_key_index: int | None,
        temperature: float,
    ) -> None:
        self.provider = provider
        self.model = model
        self.api_key_index = api_key_index
        self.temperature = temperature

    def set_outputs(
        self,
        *,
        raw_model_output: str,
        after_sanitize: str,
        after_enforce: str,
        execution_flags: dict[str, bool],
    ) -> None:
        self.raw_model_output = raw_model_output or ""
        self.sanitize_changes = audit_sanitize_changes(
            self.raw_model_output, after_sanitize
        )
        self.enforce_changes = audit_enforce_changes(
            after_sanitize, after_enforce, execution_flags
        )
        self.final_output = after_enforce or ""

    def diagnose(self) -> str:
        if self.enforce_changes:
            return "Execution rule overrode response."
        if self.sanitize_changes:
            return "Sanitizer modified model output."
        if self.memory_tokens > max(self.history_tokens, 80):
            return "Retrieved memory dominated reply."
        if self.history_tokens > 120:
            return "Conversation continuity dominated reply."
        active_flags = [k for k, v in self.execution_flags.items() if v]
        if len(active_flags) >= 2:
            return "Prompt contained conflicting instructions."
        if self.detected_language != self.session_language:
            return "Language lock differed from detected language."
        return "Model generated response from soul stack and runtime rules."

    def emit(self) -> None:
        if not DEBUG_COGNITION:
            return

        print("\n==============================")
        print("REQUEST")
        print("==============================")
        print(f"User Message: {self.user_message}")
        print(f"Detected Language: {self.detected_language}")
        print(f"Detected Intent: {self.detected_intent}")
        print(f"Execution Flags: {self.execution_flags}")
        print(f"Session Language: {self.session_language}")

        print("\n==============================")
        print("PROMPT")
        print("==============================")
        print(f"Core Prompt Tokens: {self.core_prompt_tokens}")
        print(f"Runtime Tokens: {self.runtime_tokens}")
        print(f"History Tokens: {self.history_tokens}")
        print(f"Memory Tokens: {self.memory_tokens}")
        print(f"Total Tokens: {self.total_tokens}")

        print("\n==============================")
        print("MEMORY")
        print("==============================")
        print("Raw Chroma Results:")
        print(self.raw_chroma if self.raw_chroma is not None else "(none)")
        print("\nAccepted Memories:")
        if self.accepted_memories:
            for item in self.accepted_memories:
                print(f"- [{item.get('id')}] {item.get('doc')}")
        else:
            print("(none)")
        print("\nRejected Memories:")
        if self.rejected_memories:
            for item in self.rejected_memories:
                print(f"- [{item.get('id')}] {item.get('reason')}: {item.get('doc')}")
        else:
            print("(none)")

        print("\n==============================")
        print("CONTINUITY")
        print("==============================")
        print("Conversation History Used:")
        print(self.history_used or "(none)")
        print("\nSemantic State Used:")
        print(self.semantic_state or "(none)")
        print(f"\nPending Tasks: {self.pending_tasks or '(none)'}")
        print(f"Current Topic: {self.current_topic}")
        print(f"User Intent: {self.user_intent}")

        print("\n==============================")
        print("MODEL")
        print("==============================")
        print(f"Provider: {self.provider}")
        print(f"Model: {self.model}")
        key_label = f"#{self.api_key_index + 1}" if self.api_key_index is not None else "N/A"
        print(f"API Key: {key_label}")
        print(f"Temperature: {self.temperature}")

        print("\n==============================")
        print("RAW MODEL OUTPUT")
        print("==============================")
        print(self.raw_model_output or "(empty)")

        print("\n==============================")
        print("SANITIZER")
        print("==============================")
        if self.sanitize_changes:
            for change in self.sanitize_changes:
                print(f'Removed:\n"{change["removed"]}"')
                print(f"Reason:\n{change['reason']}\n")
        else:
            print("Sanitizer:\nNo Changes")

        if self.enforce_changes:
            print("Enforcer:")
            for change in self.enforce_changes:
                print(f'Changed:\n{change["removed"]}')
                print(f"Reason:\n{change['reason']}\n")

        print("==============================")
        print("FINAL OUTPUT")
        print("==============================")
        print(self.final_output or "(empty)")

        print("\n==============================")
        print("FINAL DIAGNOSIS")
        print("==============================")
        print(f"Reason:\n{self.diagnose()}")
        print("==============================\n")
