#region 📦 SYSTEM IMPORTS & LOGGING SETUP
import os
import json
import html
import time
import subprocess
import asyncio
import re
import sys
import logging
import threading
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
import requests
from groq import Groq
from groq import (
    RateLimitError,
    NotFoundError,
    PermissionDeniedError,
)
from openpersona_loader import OpenPersonaPersona
from zesty_runtime_logger import zesty_logger
from conversation_manager.manager import ConversationManager
from conversation.working_memory import WorkingMemoryEngine
from cognition_debug import DEBUG_COGNITION, CognitionDebugTrace, memory_reject_reason
from deep_probe_engine import DeepProbeEngine
from hindi_voice import apply_hindi_partner_voice
from probe_fast_path import format_probe_voice_summary, is_pure_data_probe_query
from owner_profile import OwnerProfile
from saved_profiles import SavedProfilesStore
from presence import PresenceManager
import hashlib
import math
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from dotenv import load_dotenv

load_dotenv()

from tts_router import tts_router
from tts.playback import run_serialized, stop_playback as stop_tts_playback

logging.getLogger('wsgi').setLevel(logging.ERROR)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__, static_folder=".")
app.logger.disabled = True
#endregion

# =====================================================================
#region 🛸 1. GROQ KEY ROTATOR + OPENPERSONA ZESTY PERSONA
# =====================================================================

class GroqKeyRotator:
    def __init__(self):
        raw = os.environ.get("GROQ_API_KEYS", "")
        self.keys = [k.strip() for k in raw.split(",") if k.strip()]
        self.failed = set()
        self.current_index = 0

        if not self.keys:
            raise RuntimeError(
                "GROQ_API_KEYS is not configured. "
                "Set it in .env as comma-separated values, "
                "or export GROQ_API_KEYS='key1,key2'."
            )

        self._log(f"Loaded {len(self.keys)} Groq API key(s)")

    def _log(self, message: str):
        print(f"[GROQ ROTATOR] {message}")

    def current_client(self) -> Groq:
        return Groq(api_key=self.keys[self.current_index])

    def mark_failed(self, index: int):
        if index not in self.failed:
            self.failed.add(index)
            self._log(f"Key #{index + 1} failed")

    def advance(self) -> bool:
        if self.current_index + 1 < len(self.keys):
            self.current_index += 1
            self._log(f"Rotating to Key #{self.current_index + 1}")
            return True
        self._log("All keys exhausted")
        return False

    def next_working_client(self) -> Groq:
        tried = 0
        while tried < len(self.keys):
            if self.current_index not in self.failed:
                return self.current_client()
            if not self.advance():
                break
            tried += 1
        raise RuntimeError("All Groq API keys have been exhausted")

    def mark_success(self):
        self._log(f"Key #{self.current_index + 1} succeeded")

    @property
    def current_key_index(self) -> int:
        return self.current_index


PREFERRED_GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3-32b",
    "llama-3.3-70b-versatile",
]


class GroqModelRouter:
    """Discover Groq models at startup and route requests with cached fallback."""

    def __init__(self, rotator: GroqKeyRotator):
        self.rotator = rotator
        self.AVAILABLE_MODELS: list[str] = []
        self.current_model_index = 0
        self.last_switch_reason = ""
        self._discover_models()

    def _discover_models(self) -> None:
        api_model_ids: set[str] = set()
        last_error: str | None = None

        for key in self.rotator.keys:
            try:
                client = Groq(api_key=key)
                page = client.models.list()
                api_model_ids = {model.id for model in page.data}
                break
            except Exception as exc:
                last_error = str(exc)

        self.AVAILABLE_MODELS = [
            model_id for model_id in PREFERRED_GROQ_MODELS if model_id in api_model_ids
        ]
        self.current_model_index = 0
        self.last_switch_reason = ""

        if not self.AVAILABLE_MODELS:
            print(
                "[GROQ MODEL] WARNING: No preferred models available from Groq Models API."
            )
            if last_error:
                print(f"[GROQ MODEL] Last discovery error: {last_error[:200]}")

        self._print_model_status(event="startup")

    @property
    def current_model(self) -> str:
        if not self.AVAILABLE_MODELS:
            raise RuntimeError("No Groq models available for this API key.")
        return self.AVAILABLE_MODELS[self.current_model_index]

    @property
    def fallback_model(self) -> str | None:
        next_index = self.current_model_index + 1
        if next_index < len(self.AVAILABLE_MODELS):
            return self.AVAILABLE_MODELS[next_index]
        return None

    def advance_model(self, reason: str) -> bool:
        if self.current_model_index + 1 >= len(self.AVAILABLE_MODELS):
            return False
        self.current_model_index += 1
        self.last_switch_reason = reason
        self._print_model_status(event="switch")
        return True

    @staticmethod
    def is_rate_limit_error(exc: Exception) -> bool:
        if isinstance(exc, RateLimitError):
            return True
        message = str(exc).lower()
        return any(
            keyword in message
            for keyword in (
                "rate limit",
                "429",
                "quota",
                "tokens_per_day",
                "rate_limit_exceeded",
                "resource exhausted",
            )
        )

    @staticmethod
    def is_model_error(exc: Exception) -> bool:
        if isinstance(exc, (NotFoundError, PermissionDeniedError)):
            return True
        status_code = getattr(exc, "status_code", None)
        if status_code == 404:
            return True
        message = str(exc).lower()
        return any(
            keyword in message
            for keyword in (
                "model unavailable",
                "model_unavailable",
                "permission denied",
                "unsupported",
                "retired",
                "not found",
                "invalid model",
                "model_not_found",
                "does not exist",
                "no such model",
                "model is not",
                "model not found",
            )
        )

    def _print_model_status(self, *, event: str) -> None:
        print("----------------------------------------")
        print("Available Models")
        if self.AVAILABLE_MODELS:
            for model_id in self.AVAILABLE_MODELS:
                print(f"- {model_id}")
        else:
            print("- (none)")
        print("Current Model")
        print(self.current_model if self.AVAILABLE_MODELS else "(none)")
        print("Fallback Model")
        print(self.fallback_model or "(none)")
        print("Reason for Switch")
        if event == "switch" and self.last_switch_reason:
            print(self.last_switch_reason)
        else:
            print("(none)")
        print("----------------------------------------")


groq_rotator = GroqKeyRotator()
groq_model_router = GroqModelRouter(groq_rotator)
GROQ_MODEL = groq_model_router.current_model if groq_model_router.AVAILABLE_MODELS else os.environ.get(
    "GROQ_MODEL", "llama-3.3-70b-versatile"
)

zesty_persona = OpenPersonaPersona("personas/zesty")
zesty_system_prompt = zesty_persona.get_system_prompt()

DB_DIR = "zesty_knowledge_base"
chroma_client = chromadb.PersistentClient(path=DB_DIR)
JOURNAL_FILE = "boss_personal_journal.json"
CONVERSATION_HISTORY = []

conversation_manager = ConversationManager()
working_memory_engine = WorkingMemoryEngine()

class ZestyCloudEmbeddingFunction(EmbeddingFunction):
    """Cloud embed with deterministic hash fallback (never zero vectors)."""

    _DIM = 384

    @staticmethod
    def _hash_embed(text: str, dim: int = 384) -> list[float]:
        vec = [0.0] * dim
        tokens = re.findall(r"\w+", (text or "").lower()) or [""]
        for i, tok in enumerate(tokens):
            digest = hashlib.sha256(f"{i}:{tok}".encode()).digest()
            for j in range(dim):
                byte = digest[j % len(digest)]
                vec[j] += ((byte / 127.5) - 1.0) / max(len(tokens), 1)
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def __call__(self, input: Documents) -> Embeddings:  # type: ignore
        try:
            url = "https://feature-extraction.hf.space/embed"
            res = requests.post(url, json={"inputs": input}, timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                if (
                    isinstance(data, list)
                    and data
                    and isinstance(data[0], list)
                    and any(abs(float(x)) > 1e-6 for x in data[0][:16])
                ):
                    return data
        except Exception:
            pass
        print("[CHROMA] Cloud embed unavailable — using hash fallback", flush=True)
        return [self._hash_embed(t) for t in input]

cloud_embedding = ZestyCloudEmbeddingFunction()
collection = chroma_client.get_or_create_collection(name="zesty_master_lexicon_v4", embedding_function=cloud_embedding)
saved_profiles_collection = chroma_client.get_or_create_collection(
    name="saved_profiles", embedding_function=cloud_embedding
)
owner_identity = OwnerProfile()
saved_profiles_store = SavedProfilesStore(
    saved_profiles_collection,
    owner_profile=owner_identity,
    working_memory_engine=working_memory_engine,
    conversation_manager=conversation_manager,
)
from presence.identity_registry import IdentityRegistry
from presence.profile_bridge import IdentityProfileBridge

_identity_registry = IdentityRegistry()
_profile_bridge = IdentityProfileBridge(_identity_registry, saved_profiles_store)
presence_manager = PresenceManager(
    registry=_identity_registry,
    profile_bridge=_profile_bridge,
    owner_display_name="Sanjay Darnal",
)
#endregion

# =====================================================================
#region 🎛️ 2. SYSTEM CORE MECHANICS
# =====================================================================
class WeatherService:
    def get_weather(self):
        try:
            url = "https://wttr.in/Goa?format=%C+%t"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                return res.text.strip()
        except Exception:
            pass
        return "unavailable"

class ResearchService:
    NO_USABLE_FACTS = "__HOST_RESEARCH_NO_USABLE_FACTS__"
    _REGION_CHROME = {
        "all regions", "argentina", "australia", "austria", "belgium", "brazil",
        "bulgaria", "canada", "catalonia", "chile", "china", "colombia",
    }

    @staticmethod
    def _clean_html_text(html_fragment: str) -> str:
        text = re.sub(r"<[^>]+>", " ", html_fragment or "")
        text = html.unescape(text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _normalize_result_url(raw_url: str) -> str:
        raw_url = (raw_url or "").strip()
        if not raw_url:
            return ""
        match = re.search(r"uddg=([^&]+)", raw_url)
        if match:
            return requests.utils.unquote(match.group(1))
        if raw_url.startswith("//"):
            return f"https:{raw_url}"
        return raw_url

    def _extract_duckduckgo_results(self, html: str) -> list[dict[str, str]]:
        titles = re.findall(
            r'class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        snippets = re.findall(
            r'class="result__snippet"[^>]*>(.*?)</a>',
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )

        results: list[dict[str, str]] = []
        for index, (raw_url, title_html) in enumerate(titles[:8]):
            title = self._clean_html_text(title_html)
            snippet = (
                self._clean_html_text(snippets[index])
                if index < len(snippets)
                else ""
            )
            if not title or len(title) < 4:
                continue
            lowered = title.lower()
            if lowered.endswith("duckduckgo") or lowered in self._REGION_CHROME:
                continue
            if not snippet and len(title) < 12:
                continue
            results.append(
                {
                    "title": title,
                    "snippet": snippet,
                    "url": self._normalize_result_url(raw_url),
                }
            )
        return results

    def _format_results(self, results: list[dict[str, str]]) -> str:
        lines: list[str] = []
        for item in results[:5]:
            line = f"- {item['title']}"
            if item.get("snippet"):
                line += f": {item['snippet']}"
            if item.get("url"):
                line += f" ({item['url']})"
            lines.append(line)
        return "\n".join(lines)

    def search(self, query: str) -> str:
        try:
            url = "https://duckduckgo.com/html/"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, params={"q": query}, headers=headers, timeout=10)
            if res.status_code != 200:
                return self.NO_USABLE_FACTS

            results = self._extract_duckduckgo_results(res.text)
            if not results:
                return self.NO_USABLE_FACTS

            formatted = self._format_results(results)
            return formatted if formatted.strip() else self.NO_USABLE_FACTS
        except Exception:
            return self.NO_USABLE_FACTS

class ZestyCommercialOS:
    def __init__(self):
        self.boss_mode_active = False
        self._session_lang: dict[str, str] = {}
        self._cognition_trace: CognitionDebugTrace | None = None
        if not os.path.exists(JOURNAL_FILE):
            with open(JOURNAL_FILE, "w") as f: json.dump([], f)

        self.weather_service = WeatherService()
        self.research_service = ResearchService()
        self.deep_probe_engine = DeepProbeEngine(self.research_service)
        self.owner_profile = owner_identity
        self.saved_profiles = saved_profiles_store
        self.presence_manager = presence_manager
        self._owner_update_asked_sessions: set[str] = set()

        self.cleanup_audio()

    def cleanup_audio(self):
        try:
            stop_tts_playback()
            if os.path.exists("zesty_reply.mp3"):
                os.remove("zesty_reply.mp3")
        except Exception:
            pass

    def get_live_weather(self):
        return self.weather_service.get_weather()

    def clean_phonetics_layer(self, text: str) -> str:
        text = re.sub(r'^(hi\s+)?justi[a-z]*\s+|^जैस्री\s+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'sukht[a-z]*|sukhd[a-z]*|palak\s+sukhta[a-z]*', 'Prahlad Sukhtankar', text, flags=re.IGNORECASE)
        return text.strip()

    def save_to_lexicon(self, data_text: str) -> str:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            doc_id = f"artifact_{int(time.time())}"
            collection.add(documents=[data_text], ids=[doc_id], metadatas=[{"timestamp": timestamp, "type": "user_experiment"}])
            return "Understood, Sanjay Boss. मैंने इस डेटा को कोर लेक्सिकॉन मेमोरी में लॉक कर दिया है।"
        except Exception as e: return f"Memory storage node error: {str(e)}"

    def deep_internet_research(self, query: str) -> str:
        return self.research_service.search(query)

    def execute_os_command_or_research(self, text: str) -> tuple:
        cleaned = text.lower()
        if "chrome" in cleaned or "browser" in cleaned:
            if "open" in cleaned or "kholo" in cleaned:
                subprocess.Popen(["open", "-a", "Google Chrome"])
                return True, "Opening Google Chrome, Boss."

        research_triggers = [
            "search", "find", "lookup", "research", "detail", "info",
            "strategy", "who is", "what is", "बताओ", "ढूंढो",
            "जानकारी", "कौन है", "क्या है", "dna", "flavour",
        ]

        if any(trigger in cleaned for trigger in research_triggers):
            return False, self.deep_internet_research(text)

        return False, ""

    def build_dynamic_mood_greeting(self, user_input: str, lang_hint: str = "english") -> str:
        weather = self.get_live_weather()
        current_hour = datetime.now().hour
        if current_hour < 12:
            time_en, time_hi = "Good morning", "Good morning"
        elif current_hour < 17:
            time_en, time_hi = "Good afternoon", "Good afternoon"
        else:
            time_en, time_hi = "Good evening", "Good evening"
        if lang_hint == "hindi":
            return f"{time_hi}, Sanjay. कॉकपिट तैयार है। Goa का मौसम: {weather}."
        if lang_hint == "hinglish":
            return f"{time_en}, Sanjay. Cockpit ready hai. Goa weather abhi {weather}."
        return f"{time_en}, Sanjay. Cockpit is ready. Goa weather: {weather}."

    @staticmethod
    def detect_language(text: str) -> str:
        """Detect english | hindi | hinglish from the latest user message."""
        raw = (text or "").strip()
        if not raw:
            return "english"

        devanagari = len(re.findall(r"[\u0900-\u097F]", raw))
        latin = len(re.findall(r"[A-Za-z]", raw))
        total_letters = devanagari + latin
        if total_letters == 0:
            return "english"

        if devanagari / total_letters >= 0.35:
            return "hindi"

        from conversation_manager.models import _HINGLISH_MARKERS

        has_hinglish = bool(_HINGLISH_MARKERS.search(raw))
        ascii_only = bool(re.match(r'^[\x00-\x7F]+$', raw))
        if ascii_only and not has_hinglish and re.search(r"[A-Za-z]", raw):
            return "english"
        if has_hinglish or (latin and not ascii_only):
            return "hinglish"
        if ascii_only:
            return "english"
        return "hinglish"

    @staticmethod
    def _detect_explicit_language_switch(text: str) -> str | None:
        lower = (text or "").lower()
        if re.search(
            r"(now in|switch to|back to|ab)\s+english|english\s+mein|english में|in english\b|अब english",
            lower,
        ):
            return "english"
        if re.search(
            r"(now in|switch to|ab)\s+hindi|hindi\s+mein|हिंदी में|हिन्दी में|in hindi\b|अब hindi",
            lower,
        ):
            return "hindi"
        if re.search(r"\bhinglish\b|roman\s+hinglish", lower):
            return "hinglish"
        return None

    @staticmethod
    def _user_clearly_switched_language(text: str, detected: str) -> bool:
        dev = len(re.findall(r"[\u0900-\u097F]", text or ""))
        lat = len(re.findall(r"[A-Za-z]", text or ""))
        total = dev + lat
        if total == 0:
            return False
        if detected == "hindi":
            return dev / total >= 0.35
        if detected == "english":
            from conversation_manager.models import _HINGLISH_MARKERS

            if dev > 0:
                return False
            return lat / total >= 0.85 and not _HINGLISH_MARKERS.search(text or "")
        from conversation_manager.models import _HINGLISH_MARKERS

        return bool(_HINGLISH_MARKERS.search(text or "")) or (
            dev > 0 and lat > 0 and dev / total < 0.35
        )

    def resolve_session_language(self, session_id: str, text: str) -> str:
        """Follow the latest user message — switch when language is clear."""
        explicit = self._detect_explicit_language_switch(text)
        if explicit:
            self._session_lang[session_id] = explicit
            return explicit

        detected = self.detect_language(text)
        prev = self._session_lang.get(session_id)
        if prev is None:
            self._session_lang[session_id] = detected
            return detected

        if detected != prev and self._user_clearly_switched_language(text, detected):
            self._session_lang[session_id] = detected
            return detected

        # Short English commands after a Hindi thread still count as a switch.
        if prev == "hindi" and detected == "english":
            raw = (text or "").strip()
            from conversation_manager.models import _HINGLISH_MARKERS

            if (
                not re.search(r"[\u0900-\u097F]", raw)
                and not _HINGLISH_MARKERS.search(raw)
                and re.search(r"[A-Za-z]", raw)
            ):
                self._session_lang[session_id] = "english"
                return "english"

        return prev

    @staticmethod
    def _parse_execution_flags(user_prompt: str) -> dict[str, bool]:
        lower = (user_prompt or "").lower()
        return {
            "one_sentence": bool(
                re.search(
                    r"one sentence|single sentence|only one sentence|"
                    r"don't give a long list|no long list|short mein|short me\b|"
                    r"एक (वाक्य|लाइन|वाक्य में)",
                    lower,
                )
            ),
            "rewrite": bool(
                re.search(
                    r"\brewrite\b|make it (sharper|punchier|better)|too (soft|corporate)|"
                    r"दोबारा लिख|फिर से लिख",
                    lower,
                )
            ),
            "disagree": bool(
                re.search(
                    r"disagree|don'?t just agree|push back|seedha bol|seedha bata|"
                    r"सीधे बोल|घुमा मत|सिर्फ़?\s*हाँ\s*मत|हाँ\s*मत\s*बोल",
                    lower,
                )
            ),
            "one_action": bool(
                re.search(
                    r"smallest next step|one thing only|\bone thing\b|single next step|"
                    r"ek hi (cheez|kaam)|सिर्फ एक",
                    lower,
                )
            ),
        }

    @staticmethod
    def _execution_directives_block(
        flags: dict[str, bool], *, lang_hint: str = "english"
    ) -> str:
        lines = [
            "Answer ONLY the latest user message. Do not answer a different or older question.",
            "Never claim you already discussed, resolved, or solved something unless it appears in Conversation Continuity above. If unsure, say nothing about the past.",
        ]
        if flags.get("one_sentence"):
            lines.append("Reply in exactly ONE sentence.")
        if flags.get("rewrite"):
            lines.append("Rewrite as requested. Output only the rewritten version.")
        if flags.get("disagree"):
            lines.append("Disagree honestly when you disagree. No fake agreement.")
        if flags.get("one_action"):
            lines.append("Give ONE concrete next step only. No lists.")
        if lang_hint == "hindi":
            lines.append(
                "Hindi must match English Zesty: same confidence, length, and partner tone. "
                "Feminine verb forms only. Use तुम, not आप. "
                "Short and direct — never lecture, never formal assistant register."
            )
        return "## Execution (this turn)\n\n" + " ".join(lines)

    @staticmethod
    def _first_n_sentences(text: str, n: int) -> str:
        text = (text or "").strip()
        if not text or n < 1:
            return text
        parts = [p.strip() for p in re.split(r"(?<=[.!?।])\s+", text) if p.strip()]
        if not parts:
            return text
        return " ".join(parts[:n]).strip()

    @staticmethod
    def _first_sentence(text: str) -> str:
        text = (text or "").strip()
        if not text:
            return text
        match = re.match(r"^(.+?[.!?।])(?:\s|$)", text, flags=re.DOTALL)
        if match:
            return match.group(1).strip()
        return text

    def _enforce_response_execution(
        self,
        text: str,
        flags: dict[str, bool],
        lang_hint: str,
        user_prompt: str = "",
    ) -> str:
        out = (text or "").strip()
        if not out:
            return out
        if flags.get("one_sentence"):
            out = self._first_sentence(out)
        elif lang_hint == "hindi":
            wants_detail = bool(
                re.search(
                    r"explain|detail|why|how|विस्तार|क्यों|कैसे|व्याख्या",
                    user_prompt or "",
                    re.IGNORECASE,
                )
            )
            max_sents = 1 if flags.get("disagree") else 2
            if not wants_detail:
                out = self._first_n_sentences(out, max_sents)
        if flags.get("one_action"):
            # Keep first non-empty line / bullet as the single action.
            for line in re.split(r"[\n\r]+", out):
                line = re.sub(r"^[-•*]\s*", "", line.strip())
                if line:
                    out = line
                    break
        if lang_hint == "hindi":
            out = apply_hindi_partner_voice(out)
        return out

    def _is_assistant_style_memory(self, text: str) -> bool:
        """True when a Chroma doc is old dialogue / generated reply, not a fact."""
        raw = (text or "").strip()
        if not raw:
            return True
        lower = raw.lower()
        # Stored conversation turns (User:/Zesty:/Assistant:)
        if re.match(r"^(zesty|assistant|bot|ai|hermes|jestee|user)\s*:", raw, re.IGNORECASE):
            return True
        if re.search(r"(^|\n)\s*(zesty|assistant|bot|ai|user)\s*:", raw, re.IGNORECASE):
            return True
        dialogue_markers = (
            "how can i assist",
            "how can i help",
            "what can i help",
            "i'd be happy to",
            "i am happy to help",
            "i'm happy to help",
            "i remember you asking",
            "is there anything else",
            "as an ai",
            "let me know if you need",
            "how's that for a",
            "thank you for sharing",
            "how does that make you feel",
            "i'm here for you",
            "good morning",
            "good afternoon",
            "good evening",
            "hey sanjay",
            "hello sanjay",
        )
        if any(marker in lower for marker in dialogue_markers):
            return True
        if re.search(r"\b(yaar|yar|यार)\b", lower):
            return True
        if len(raw) > 400:
            return True
        # Greeting / service templates
        if re.match(r"^(hi|hello|hey|namaste)\b", lower) and ("?" in raw or "help" in lower):
            return True
        return False

    @staticmethod
    def _memory_relevance_score(query: str, doc: str, distance: float | None) -> float:
        """Higher is better. Uses vector distance when meaningful, else lexical overlap."""
        q_words = set(re.findall(r"\w+", (query or "").lower()))
        d_words = set(re.findall(r"\w+", (doc or "").lower()))
        lexical = (len(q_words & d_words) / len(q_words)) if q_words else 0.0
        if distance is None:
            return lexical
        dist = float(distance)
        if dist >= 0.999:
            return lexical
        return max(lexical, 1.0 - dist)

    def _format_factual_memories(
        self, documents: list, query: str = "", distances: list | None = None
    ) -> tuple[str, float]:
        """Keep knowledge only — projects, people, preferences, facts."""
        facts: list[str] = []
        seen: set[str] = set()
        best_score = 0.0
        items = list(documents)
        dist_list = distances or []
        ranked = sorted(
            enumerate(items),
            key=lambda pair: self._memory_relevance_score(
                query, str(pair[1] or ""), dist_list[pair[0]] if pair[0] < len(dist_list) else None
            ),
            reverse=True,
        )
        for idx, doc in ranked:
            if not doc or not str(doc).strip():
                continue
            text = str(doc).strip()
            if self._is_assistant_style_memory(text):
                continue
            if memory_reject_reason(text):
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            score = self._memory_relevance_score(
                query, text, dist_list[idx] if idx < len(dist_list) else None
            )
            best_score = max(best_score, score)
            facts.append(text)
            if len(facts) >= 3:
                break
        if not facts:
            return "", 0.0
        return "\n".join(f"- {fact}" for fact in facts), best_score

    def query_local_chroma_database(self, user_text: str) -> str:
        mem_start = time.perf_counter()
        try:
            # Fetch several candidates so dialogue-contaminated hits can be skipped.
            results = collection.query(query_texts=[user_text], n_results=8)

            print("\n" + "=" * 70)
            print("🗂 CHROMA RAW RESULT")
            print("-" * 70)
            print(results)
            print("=" * 70 + "\n")

            memory_ids = []
            memory_ranking = 0.0
            if results and results.get("documents") and results["documents"][0]:
                docs = results["documents"][0]
                ids = (results.get("ids") or [[]])[0]
                distances = (results.get("distances") or [[]])[0]
                factual, memory_ranking = self._format_factual_memories(
                    docs, query=user_text, distances=distances
                )
                kept_ids = []
                accepted_debug: list[dict[str, str]] = []
                rejected_debug: list[dict[str, str]] = []
                for doc, doc_id in zip(docs, ids):
                    doc_text = str(doc) if doc else ""
                    reject_reason = memory_reject_reason(doc_text)
                    if reject_reason:
                        if DEBUG_COGNITION:
                            rejected_debug.append(
                                {
                                    "id": str(doc_id),
                                    "doc": doc_text[:220],
                                    "reason": reject_reason,
                                }
                            )
                    else:
                        kept_ids.append(doc_id)
                        if DEBUG_COGNITION:
                            accepted_debug.append(
                                {"id": str(doc_id), "doc": doc_text[:220]}
                            )
                memory_ids = kept_ids
                zesty_logger.log_memory(
                    working_memory="",
                    long_term_memories=len(memory_ids),
                    memory_ids=memory_ids,
                    ranking_score=memory_ranking,
                    retrieval_time_ms=(time.perf_counter() - mem_start) * 1000,
                )
                if DEBUG_COGNITION and self._cognition_trace is not None:
                    self._cognition_trace.set_memory(
                        raw_chroma=results,
                        accepted=accepted_debug,
                        rejected=rejected_debug,
                    )
                return factual

            zesty_logger.log_memory(
                working_memory="",
                long_term_memories=0,
                memory_ids=[],
                ranking_score=0.0,
                retrieval_time_ms=(time.perf_counter() - mem_start) * 1000,
            )

        except Exception as e:
            print("[CHROMA ERROR]", e)

        return ""

    def speak_text_edge_seamless(
        self,
        text_to_speak: str,
        current_lang: str,
        *,
        social_probe: bool = False,
    ):
        """Queue TTS so replies play one after another without chopping."""
        preview = (text_to_speak or "").strip()
        if not preview:
            print("[TTS] speak_text_edge_seamless skipped — empty reply", flush=True)
            return

        if social_probe:
            if len(preview) > 400:
                preview = self._first_sentence(preview) or preview[:120]
            else:
                preview = self._first_sentence(preview) or preview
            if not preview:
                print("[TTS] speak skipped — social probe reply too long for voice", flush=True)
                return

        tts_lang = current_lang if current_lang in ("english", "hindi", "hinglish") else "english"
        print(
            f"[TTS] speak_text_edge_seamless queued ({len(preview)} chars, lang={tts_lang})",
            flush=True,
        )

        def _run_tts() -> bool:
            tts_start = time.perf_counter()
            try:
                tts_router.speak_text(preview, tts_lang)
                tts_ms = (time.perf_counter() - tts_start) * 1000
                voice_name = getattr(tts_router, "active_provider", "none")
                if voice_name == "none":
                    err = getattr(tts_router, "last_error", "")
                    print(f"[TTS] speak failed after {tts_ms:.0f}ms — {err}", flush=True)
                zesty_logger.log_voice(
                    voice_name=voice_name,
                    audio_generated=voice_name != "none",
                    duration_ms=tts_ms,
                )
                return True
            except Exception as exc:
                print(f"[TTS] FATAL exception in TTS thread: {exc}", flush=True)
                traceback.print_exc()
                zesty_logger.log_voice(
                    voice_name="error",
                    audio_generated=False,
                    duration_ms=(time.perf_counter() - tts_start) * 1000,
                )
                return False

        run_serialized(_run_tts, wait=False)

    def _sanitize_response(self, text: str) -> str:
        """Strip meta leaks + generic assistant/therapist/support phrasing only."""
        sanitized = text or ""
        fragments = [
            "It seems like we've just started our conversation,",
            "and I'm ready to chat with you.",
            "I've got my personality and conversation guidelines all set,",
            "so let's dive right in.",
            "Looks like we've got a lot of context and guidelines here.",
            "It seems like we're setting the stage for our conversations.",
            "I see we've got a pretty detailed framework for how we'll interact.",
            "We've got a set of rules and guidelines that help me understand how to interact with you",
            "rules and guidelines",
            "conversation guidelines",
            "playbook",
            "I'll break it down for you",
            "pretty detailed guide",
            "framework for how we'll interact",
        ]
        for fragment in fragments:
            sanitized = sanitized.replace(fragment, "")

        style_res = [
            r"how can i (help|assist)( you)?( today)?\??",
            r"what can i (do|help) (for|you)[^.!?]*[.!]?",
            r"i'?d be happy to (help|assist)[^.!?]*[.!]?",
            r"i('m| am) (here to help|happy to help|here for you)[^.!?]*[.!]?",
            r"is there anything else( i can (help|assist) you with)?\??",
            r"let me know if (you need|there'?s)[^.!?]*[.!]?",
            r"as an ai( assistant)?[^.!?]*[.!]?",
            r"i (hear you|understand how you feel)[^.!?]*[.!]?",
            r"thank you for sharing[^.!?]*[.!]?",
            r"how does that make you feel\??",
            r"\bmadam(\s*ji)?\b",
            r"i hope (this helps|that helps)[^.!?]*[.!]?",
            r"feel free to (ask|reach out)[^.!?]*[.!]?",
            # Hindi formal / assistant / lecturer / therapist openers (Devanagari)
            r"आइए\s+(पहले\s+)?(इस\s+)?(विषय|मुद्दे|बात)\s*(को\s*)?(समझते|देखते|चर्चा)\s*[^\n।.!?]*[।.!?]?",
            r"चलिए\s+(इस|हम)\s*[^\n।.!?]*?(चर्चा|विस्तार|समझ)[^\n।.!?]*[।.!?]?",
            r"मैं\s+आपकी\s+सहायता\s+कर\s+सकता\s+हूँ[^\n।.!?]*[।.!?]?",
            r"मैं\s+आपकी\s+मदद\s+के\s+लिए\s+(यहाँ\s+)?हूँ[^\n।.!?]*[।.!?]?",
            r"मैं\s+समझता\s+हूँ\s+कि\s+आपको\s+[^\n।.!?]*[।.!?]?",
            r"कृपया\s+(बता[^\n।.!?]*|मुझे\s+जानने)[^\n।.!?]*[।.!?]?",
            r"आपकी\s+सेवा\s+में\s+[^\n।.!?]*[।.!?]?",
            r"महोदय[^\n।.!?]*[।.!?]?",
            r"Madam\s*ji",
            r"मैं\s+आपको\s+समझाने\s+की\s+कोशिश[^\n।.!?]*[।.!?]?",
            r"इस\s+विषय\s+पर\s+विस्तार\s+से\s+[^\n।.!?]*[।.!?]?",
            # False shared-history claims (unsupported invention)
            r"\bwe (already|'ve already|had already) (discussed|talked about|resolved|solved|decided)[^.!?]*[.!?]?",
            r"\bwe solved that[^.!?]*[.!?]?",
            r"\byou told me (earlier|before)[^.!?]*[.!?]?",
            r"\b(humne|hum) (pehle|already) (discuss|baat|resolve|solve|kar liya|kiya tha)[^.!?]*[.!?]?",
            r"\b(humne|hum) usse resolve kar liya tha[^.!?]*[.!?]?",
            r"\b(tumne|aapne) (pehle|पहले) (bataya|kaha|mentioned)[^.!?]*[.!?]?",
            r"\bwe('ve| have) been putting off[^.!?]*[.!?]?",
            r"मैं समझता हूँ कि हमने पहले[^।.!?]*[।.!?]?",
        ]
        for pattern in style_res:
            sanitized = re.sub(pattern, " ", sanitized, flags=re.IGNORECASE)

        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        sanitized = sanitized.strip(",. \n\t")
        return sanitized or (text or "").strip()
#endregion

# =====================================================================
#region 🧠 3. INTENT-AWARE COGNITIVE LAYER (GROQ + OPENPERSONA)
# =====================================================================

    @staticmethod
    def _language_lock_block(lang_hint: str) -> str:
        """Per-turn language lock. Hindi gets personality-preservation guidance;
        English/Hinglish stay minimal so their already-good behavior is untouched.
        """
        if lang_hint == "english":
            return (
                "## Language Lock (this turn)\n\n"
                "Reply in English only for this turn. "
                "Stay in English for this thread unless the user's latest message clearly switched language. "
                "Never translate unless asked. Never force slang or honorifics the user did not use."
            )

        if lang_hint == "hinglish":
            return (
                "## Language Lock (this turn)\n\n"
                "Reply in the same Romanized Hinglish mix and script as the user for this turn. "
                "Stay in that mix for this thread unless the user clearly switched language. "
                "Never translate unless asked. Never force slang or honorifics the user did not use."
            )

        # hindi — feminine partner tone, casual तुम
        return (
            "## Language Lock (this turn)\n\n"
            "Reply in Hindi (Devanagari) only for this turn. "
            "Stay in Hindi for this thread unless the user's latest message clearly switched language. "
            "Never translate unless asked. Never force slang or honorifics the user did not use.\n\n"
            "Zesty speaks Hindi as a woman: always feminine verb forms "
            "(सकती हूँ, करती हूँ, बोलती हूँ, नहीं हूँ — never सकता/करता/बोलता). "
            "Address Sanjay with तुम/तुम्हारा — never आप/आपका unless he used आप first.\n\n"
            "Write Hindi exactly as the English version would sound if spoken naturally by the same person. "
            "Casual partner tone — not formal, not assistant register. "
            "Do not increase formality, politeness, explanation depth, or sentence length merely because the language is Hindi."
        )

    _PROFILE_FOLLOW_UP_RE = re.compile(
        r"\b("
        r"save|update|delete|refresh|open|show|remember|"
        r"haan|yes|ok|okay|do it|go ahead|kar do|karo|"
        r"this profile|isko|is ko|ye profile"
        r")\b",
        re.IGNORECASE,
    )

    def _is_profile_follow_up(self, text: str) -> bool:
        lowered = (text or "").lower().strip()
        if not lowered:
            return False
        if self.saved_profiles.parse_command(text):
            return True
        if len(lowered.split()) <= 4 and self._PROFILE_FOLLOW_UP_RE.search(lowered):
            return True
        return False

    def _update_session_continuity(
        self,
        session_id: str,
        cleaned_input: str,
        *,
        deep_probe_payload: dict | None = None,
    ) -> None:
        """Sync working memory + conversation manager with the current turn."""
        if not session_id:
            return

        conversation_manager.ensure_session(session_id)
        wm_state = working_memory_engine.ensure_session(session_id)
        wm_state.user_intent = cleaned_input[:220]
        wm_state.touch()

        profile_name = None
        if deep_probe_payload and deep_probe_payload.get("name"):
            profile_name = str(deep_probe_payload["name"]).strip()
        elif self._is_profile_follow_up(cleaned_input):
            last_probe = self.saved_profiles.get_last_probe(session_id)
            if last_probe and last_probe.get("name"):
                profile_name = str(last_probe["name"]).strip()

        if profile_name:
            wm_state.current_topic = profile_name
            wm_state.current_mode = wm_state.current_mode or "social_probe"
            note = f"Profile in focus: {profile_name}"
            if note not in wm_state.recent_decisions:
                wm_state.recent_decisions.append(note)
                wm_state.recent_decisions = wm_state.recent_decisions[-8:]
            conversation_manager.set_active_topic(session_id, profile_name)
            conversation_manager.update_topic_structured(session_id, profile_name)
            conversation_manager.update_task(session_id, f"Profile: {profile_name}")
            return

        topic_hint = cleaned_input.strip()
        if len(topic_hint) > 80:
            topic_hint = topic_hint[:80].rsplit(" ", 1)[0]
        if topic_hint:
            wm_state.current_topic = topic_hint
            conversation_manager.set_active_topic(session_id, topic_hint)
            conversation_manager.update_topic_structured(session_id, topic_hint)

    def _record_profile_cmd_in_history(self, session_id: str, user_text: str, reply_text: str) -> None:
        if not session_id or not user_text:
            return
        try:
            conversation_manager.ensure_session(session_id)
            conversation_manager.add_message(session_id, "user", user_text)
            if reply_text:
                conversation_manager.add_message(session_id, "assistant", reply_text)
        except Exception:
            pass

    def handle_presence_command(self, text: str) -> dict | None:
        """Simulate presence modes or Chief introductions — fast early return."""
        from presence.commands import parse_introduction, parse_simulate_command
        from presence.models import PresenceState, PrivacyTier

        sim = parse_simulate_command(text)
        if sim:
            snap, reply = self.presence_manager.run_simulate(sim)
            return {
                "voice_text": reply,
                "dynamic_html": f"<div class='hermes-dynamic-content'>{reply}</div>",
                "open_panel": "chat",
                "presence": self.presence_manager.to_api_payload(),
            }

        intro = parse_introduction(text)
        if intro:
            snap = self.presence_manager.snapshot
            can_introduce = snap.privacy_tier == PrivacyTier.FULL or snap.state in (
                PresenceState.CHIEF_MODE,
                PresenceState.UNKNOWN_RESTRICTED,
                PresenceState.PRIVACY_HOLD,
            )
            if can_introduce:
                _, reply = self.presence_manager.introduce_person(intro.display_name)
                return {
                    "voice_text": reply,
                    "dynamic_html": f"<div class='hermes-dynamic-content'>{reply}</div>",
                    "open_panel": "chat",
                    "presence": self.presence_manager.to_api_payload(),
                }

        return None

    def _will_run_social_probe(
        self, text: str, *, owner_self_query: bool, presence_restricted: bool
    ) -> bool:
        if owner_self_query:
            return True
        if presence_restricted:
            return False
        return self.deep_probe_engine.should_probe(text)

    def _assemble_probe_prompt(
        self,
        *,
        web_intel: str,
        session_id: str | None,
        lang_hint: str = "english",
        owner_self_query: bool = False,
        execution_flags: dict[str, bool] | None = None,
    ) -> str:
        """Compact prompt for probe/search turns — faster LLM, smaller context."""
        parts = [
            "You are Zesty — Sanjay's direct partner co-pilot. No fluff, no service voice.",
            self._language_lock_block(lang_hint),
        ]

        mode_response = self.presence_manager.export_response_addendum()
        if mode_response:
            parts.append(mode_response)

        if owner_self_query:
            parts.append(
                "The user is Chief (Sanjay Darnal), the system owner. "
                "Answer about him only — do not repeat the full Chief biography block."
            )
        else:
            parts.append(
                "The query is about someone other than Chief. "
                "Do not inject Chief's full identity or biography."
            )

        if execution_flags is not None:
            parts.append(
                self._execution_directives_block(execution_flags, lang_hint=lang_hint)
            )

        parts.append(
            "## Task (this turn)\n\n"
            "Summarize the host research below in 5–8 tight bullets. "
            "Lead with the answer. Include platform stats and recent activity when present. "
            "Max ~120 words unless the user explicitly asked for exhaustive detail."
        )

        if web_intel and web_intel.strip() and web_intel.strip() != ResearchService.NO_USABLE_FACTS:
            parts.append(
                "## Host Research Results\n\n"
                "Facts already fetched — use them. Do not claim you lack internet access.\n\n"
                f"{web_intel.strip()}"
            )

        if session_id:
            try:
                probe_block = self.saved_profiles.format_probe_context_for_prompt(session_id)
                if probe_block:
                    last_probe = self.saved_profiles.get_last_probe(session_id)
                    if self.presence_manager.allows_probe_context(last_probe):
                        parts.append(f"## Active profile context\n\n{probe_block}")
            except Exception:
                pass

        return "\n\n".join(parts)

    def _assemble_openpersona_prompt(
        self,
        *,
        local_context: str,
        web_intel: str,
        session_id: str | None,
        include_faculties: bool = False,
        lang_hint: str = "english",
        execution_flags: dict[str, bool] | None = None,
        owner_self_query: bool = False,
        probe_mode: bool = False,
        include_chief_identity: bool = True,
    ) -> str:
        """Build the OpenPersona system prompt with runtime state, research, memory, and history."""
        if probe_mode:
            return self._assemble_probe_prompt(
                web_intel=web_intel,
                session_id=session_id,
                lang_hint=lang_hint,
                owner_self_query=owner_self_query,
                execution_flags=execution_flags,
            )

        system_prompt = zesty_persona.build_system_prompt(include_faculties=include_faculties)

        runtime_block = zesty_persona.format_runtime_context()
        if runtime_block:
            system_prompt += "\n\n" + runtime_block

        presence_block = self.presence_manager.export_for_prompt()
        if presence_block:
            system_prompt += "\n\n" + presence_block

        pending_greeting = self.presence_manager.consume_pending_greeting()
        if pending_greeting:
            system_prompt += (
                "\n\n## Opening Cue\n\n"
                f"If natural this turn, open your reply with: {pending_greeting}"
            )

        if (
            include_chief_identity
            and self.owner_profile.should_inject()
            and self.presence_manager.allows_chief_identity()
        ):
            ask_update = (
                owner_self_query
                and session_id
                and session_id not in self._owner_update_asked_sessions
            )
            chief_block = self.owner_profile.format_chief_identity_block(ask_update=ask_update)
            if chief_block:
                system_prompt += "\n\n" + chief_block
            if ask_update and session_id:
                self._owner_update_asked_sessions.add(session_id)

        system_prompt += "\n\n" + self._language_lock_block(lang_hint)

        if execution_flags is not None:
            system_prompt += "\n\n" + self._execution_directives_block(
                execution_flags, lang_hint=lang_hint
            )

        system_prompt += (
            "\n\n## Response Rules\n\n"
            "Answer from personality (injection + Conversation DNA). "
            "Never imitate previous assistant wording, memory wording, or prior tone. "
            "Use facts only as knowledge. No therapist voice, no customer-support voice, no forced slang. "
            "Never use yaar, yar, or यार — omit them entirely; do not substitute other slang."
        )

        mode_response = self.presence_manager.export_response_addendum()
        if mode_response:
            system_prompt += f"\n{mode_response}"

        if web_intel and web_intel.strip():
            if web_intel.strip() == ResearchService.NO_USABLE_FACTS:
                system_prompt += (
                    "\n\n## Host Research\n\n"
                    "No usable external facts were found."
                )
            else:
                system_prompt += (
                    "\n\n## Host Research Results\n\n"
                    "The host has already completed the web search. "
                    "The information below is current external knowledge. "
                    "Answer using these facts. "
                    "Do not claim that you lack internet access.\n\n"
                    f"{web_intel.strip()}"
                )

        if local_context:
            system_prompt += (
                "\n\n## Known Facts\n\n"
                "Background knowledge only. Never copy as dialogue:\n"
                f"{local_context}"
            )

        if session_id:
            try:
                continuity_parts = []

                try:
                    wm_block = working_memory_engine.export_for_prompt(session_id)
                    if wm_block:
                        continuity_parts.append(f"Working memory:\n{wm_block}")
                except Exception:
                    pass

                probe_block = self.saved_profiles.format_probe_context_for_prompt(session_id)
                if probe_block:
                    last_probe = self.saved_profiles.get_last_probe(session_id)
                    if self.presence_manager.allows_probe_context(last_probe):
                        continuity_parts.append(f"Session profile context:\n{probe_block}")

                structured = conversation_manager.get_structured_context(session_id)
                if structured:
                    continuity_parts.append(f"Session focus: {structured}")
                try:
                    ctx = conversation_manager.get_context(session_id, recent_limit=1)
                    topic = ctx.get("active_topic")
                    if topic:
                        continuity_parts.append(f"Active topic: {topic}")
                except Exception:
                    pass
                history_str = conversation_manager.get_conversation_history(session_id)
                if history_str:
                    continuity_parts.append(history_str)
                if continuity_parts:
                    audience = self.presence_manager.continuity_audience_line()
                    system_prompt += (
                        "\n\n## Conversation Continuity\n\n"
                        f"{audience} "
                        "Use the state below for context. Continue naturally from where the conversation left off. "
                        "Semantic state only — do not imitate prior wording, tone, slang, or service phrasing.\n"
                        + "\n".join(continuity_parts)
                    )

                if not self.presence_manager.should_restrict_private_data():
                    situational = self.saved_profiles.format_situational_awareness_for_prompt(session_id)
                    if situational:
                        system_prompt += "\n\n" + situational
            except KeyError:
                pass

        return system_prompt

    def call_llm(
        self,
        user_prompt: str,
        local_context: str,
        web_intel: str,
        session_id: str = None,
        lang_hint: str = "english",
        owner_self_query: bool = False,
        *,
        probe_mode: bool = False,
        include_chief_identity: bool = True,
    ) -> tuple:

        # ================================================================
        # DETERMINISTIC PROMPT ASSEMBLY ORDER
        # 1. Soul personality (injection → DNA → behavior-guide → constitution)
        #    + authority fence + name lock (faculties OFF by default)
        # 2. Runtime state (mood/relationship only)
        # 3. Per-turn language lock + response rules
        # 4. Host research / known facts / semantic continuity
        # 5. Current user message
        # ================================================================

        CONTEXT_WINDOW = 8192
        RESPONSE_RESERVE = 1600
        # Faculty how-to docs dilute personality and burn budget — keep off.
        include_faculties = False
        execution_flags = self._parse_execution_flags(user_prompt)

        system_prompt = self._assemble_openpersona_prompt(
            local_context=local_context,
            web_intel=web_intel,
            session_id=session_id,
            include_faculties=include_faculties,
            lang_hint=lang_hint,
            execution_flags=execution_flags,
            owner_self_query=owner_self_query,
            probe_mode=probe_mode,
            include_chief_identity=include_chief_identity,
        )

        # --- Token Budget Enforcement ---
        MAX_TOKENS = CONTEXT_WINDOW - RESPONSE_RESERVE
        estimated_tokens = len(system_prompt.split()) + len(user_prompt.split())

        if estimated_tokens > MAX_TOKENS:
            # 1. Trim conversation history first
            if session_id:
                try:
                    history = conversation_manager._history.get(session_id)
                    if history and len(history.messages) > 6:
                        history.messages = history.messages[-6:]
                        system_prompt = self._assemble_openpersona_prompt(
                            local_context=local_context,
                            web_intel=web_intel,
                            session_id=session_id,
                            include_faculties=False,
                            lang_hint=lang_hint,
                            execution_flags=execution_flags,
                            owner_self_query=owner_self_query,
                            probe_mode=probe_mode,
                            include_chief_identity=include_chief_identity,
                        )
                except Exception:
                    pass

            # 2. Trim working memory lists
            if session_id:
                try:
                    state = working_memory_engine.get_session(session_id)
                    if len(state.pending_tasks) > 3:
                        state.pending_tasks = state.pending_tasks[-3:]
                    if len(state.open_questions) > 3:
                        state.open_questions = state.open_questions[-3:]
                    if len(state.recent_decisions) > 3:
                        state.recent_decisions = state.recent_decisions[-3:]
                except Exception:
                    pass

            # 3. Trim long-term memory (local_context)
            if local_context and len(local_context.split()) > 200:
                local_context = " ".join(local_context.split()[:200])
                system_prompt = self._assemble_openpersona_prompt(
                    local_context=local_context,
                    web_intel=web_intel,
                    session_id=session_id,
                    include_faculties=False,
                    lang_hint=lang_hint,
                    execution_flags=execution_flags,
                    owner_self_query=owner_self_query,
                    probe_mode=probe_mode,
                    include_chief_identity=include_chief_identity,
                )

        estimated_tokens = len(system_prompt.split()) + len(user_prompt.split())

        try:

            llm_start = time.perf_counter()
            prompt_build_ms = (time.perf_counter() - llm_start) * 1000

            conversation_dna_text = ""
            persona_text = ""
            try:
                conversation_dna_path = zesty_persona.persona_dir / "soul" / "CONVERSATION_DNA.md"
                if conversation_dna_path.is_file():
                    conversation_dna_text = conversation_dna_path.read_text(encoding="utf-8")
            except Exception:
                conversation_dna_text = ""
            try:
                injection_path = zesty_persona.persona_dir / "soul" / "injection.md"
                if injection_path.is_file():
                    persona_text = injection_path.read_text(encoding="utf-8")
            except Exception:
                persona_text = ""

            # Gather history text for logging
            history_text = ""
            if session_id:
                try:
                    history_text = conversation_manager.get_conversation_history(session_id)
                except Exception:
                    history_text = ""

            if DEBUG_COGNITION and self._cognition_trace is not None:
                core_prompt_text = zesty_persona.build_system_prompt(
                    include_faculties=False
                )
                runtime_block_text = (
                    system_prompt[len(core_prompt_text) :]
                    if system_prompt.startswith(core_prompt_text)
                    else ""
                )
                self._cognition_trace.set_prompt_tokens(
                    core_prompt=core_prompt_text,
                    runtime_block=runtime_block_text,
                    history_text=history_text,
                    memory_text=local_context or "",
                    user_message=user_prompt,
                )
                pending_tasks: list[str] = []
                user_intent = "(none)"
                current_topic = "(none)"
                semantic_state = ""
                if session_id:
                    try:
                        ctx = conversation_manager.get_context(session_id)
                        current_topic = str(ctx.get("active_topic") or "(none)")
                    except Exception:
                        pass
                    try:
                        semantic_state = conversation_manager.get_structured_context(
                            session_id
                        )
                    except Exception:
                        pass
                    try:
                        wm_state = working_memory_engine.get_session(session_id)
                        pending_tasks = list(wm_state.pending_tasks)
                        user_intent = wm_state.user_intent or "(none)"
                    except Exception:
                        pass
                self._cognition_trace.set_continuity(
                    history_used=history_text,
                    semantic_state=semantic_state,
                    pending_tasks=pending_tasks,
                    current_topic=current_topic,
                    user_intent=user_intent,
                )

            # --- Token Budget Auditing (Observability Only) ---
            # Estimate tokens for each section using character-based estimation
            # (fallback when model tokenizer is unavailable)
            # Standard heuristic: ~4 characters per token for English text
            def _estimate_tokens(text: str) -> int:
                if not text:
                    return 0
                return max(1, len(text) // 4)

            # Get individual section token counts
            constitution_text = ""
            try:
                constitution_path = zesty_persona.persona_dir / "soul" / "constitution.md"
                if constitution_path.is_file():
                    constitution_text = constitution_path.read_text(encoding="utf-8")
            except Exception:
                pass

            behavior_guide_text = ""
            try:
                behavior_path = zesty_persona.persona_dir / "soul" / "behavior-guide.md"
                if behavior_path.is_file():
                    behavior_guide_text = behavior_path.read_text(encoding="utf-8")
            except Exception:
                pass

            # Calculate individual section tokens
            core_system_prompt_tokens = _estimate_tokens(zesty_system_prompt)
            constitution_tokens = _estimate_tokens(constitution_text)
            persona_tokens = _estimate_tokens(persona_text)
            conversation_dna_tokens = _estimate_tokens(conversation_dna_text)
            behavior_guide_tokens = _estimate_tokens(behavior_guide_text)
            memory_tokens = _estimate_tokens(local_context or "")
            history_tokens_est = _estimate_tokens(history_text)
            user_message_tokens = _estimate_tokens(user_prompt)

            total_prompt_tokens = (
                core_system_prompt_tokens
                + memory_tokens
                + history_tokens_est
                + user_message_tokens
            )

            # Model context window for llama-3.3-70b-versatile: 8192 tokens
            CONTEXT_WINDOW = 8192
            remaining_context = CONTEXT_WINDOW - total_prompt_tokens

            if total_prompt_tokens > CONTEXT_WINDOW:
                print(
                    f"WARNING: Prompt ({total_prompt_tokens} est. tokens) exceeds "
                    f"{CONTEXT_WINDOW}-token context window — model may truncate. "
                    "Consider a larger-context model or compacting soul files."
                )
            if not include_faculties:
                print(
                    "NOTICE: Faculty references omitted from this request to preserve "
                    "soul-stack priority within the context window."
                )

            # Print token audit
            print("\n" + "=" * 70)
            print("TOKEN BUDGET AUDIT")
            print("-" * 70)
            print(f"Core System Prompt Tokens : {core_system_prompt_tokens}")
            print(f"Constitution Tokens       : {constitution_tokens}")
            print(f"Persona Tokens            : {persona_tokens}")
            print(f"Conversation DNA Tokens   : {conversation_dna_tokens}")
            print(f"Behavior Guide Tokens     : {behavior_guide_tokens}")
            print(f"Long-Term Memory Tokens   : {memory_tokens}")
            print(f"Conversation History Tokens: {history_tokens_est}")
            print(f"User Message Tokens       : {user_message_tokens}")
            print(f"Total Prompt Tokens       : {total_prompt_tokens}")
            print(f"Context Window            : {CONTEXT_WINDOW}")
            print(f"Remaining Context Window  : {remaining_context}")
            print("=" * 70)

            # Warnings
            usage_pct = (total_prompt_tokens / CONTEXT_WINDOW) * 100
            if usage_pct > 95:
                print(f"WARNING: Prompt exceeds 95% of context window ({usage_pct:.1f}%)")
            elif usage_pct > 80:
                print(f"WARNING: Prompt exceeds 80% of context window ({usage_pct:.1f}%)")
            print("=" * 70 + "\n")

            zesty_logger.log_prompt(
                persona_loaded=bool(zesty_system_prompt),
                conversation_dna_loaded=True,
                history_tokens=total_prompt_tokens,
                memory_tokens=memory_tokens,
                final_tokens=total_prompt_tokens,
            )

            zesty_logger.log_final_prompt(
                system_prompt=system_prompt,
                conversation_dna_text=conversation_dna_text,
                persona_text=persona_text,
                memory_text=local_context or "",
                history_text=history_text,
                user_message=user_prompt,
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            api_start = time.perf_counter()
            first_token_ms = 0.0
            generation_ms = 0.0
            last_error = None
            tried_keys = 0
            raw_reply = ""
            start_model_index = groq_model_router.current_model_index
            model_switch_reason = ""

            if not groq_model_router.AVAILABLE_MODELS:
                zesty_logger.log_error(
                    component="Groq Provider",
                    reason="No models available",
                    recovery="Temporary unavailability",
                )
                return (
                    "System array disruption. Local neural core is temporarily unavailable.",
                    "chat",
                )

            while groq_model_router.current_model_index < len(groq_model_router.AVAILABLE_MODELS):
                current_model = groq_model_router.current_model
                tried_keys = 0
                model_failed = False

                while tried_keys < len(groq_rotator.keys):
                    client = groq_rotator.current_client()
                    try:
                        response = client.chat.completions.create(
                            model=current_model,
                            messages=messages,
                            temperature=0.55,
                            max_tokens=1000,
                            top_p=0.95,
                            presence_penalty=0.1,
                            frequency_penalty=0.1,
                        )
                        raw_reply = response.choices[0].message.content or ""
                        groq_rotator.mark_success()
                        break
                    except Exception as api_error:
                        error_message = str(api_error)
                        last_error = api_error

                        if GroqModelRouter.is_rate_limit_error(api_error):
                            print(
                                f"[GROQ ROTATOR] Key #{groq_rotator.current_key_index + 1} "
                                f"failed (rate limit): {error_message[:200]}"
                            )
                            groq_rotator.mark_failed(groq_rotator.current_key_index)
                            if not groq_rotator.advance():
                                break
                            tried_keys += 1
                            continue

                        if GroqModelRouter.is_model_error(api_error):
                            print(
                                f"[GROQ MODEL] Model '{current_model}' failed: "
                                f"{error_message[:200]}"
                            )
                            model_switch_reason = error_message[:200]
                            if not groq_model_router.advance_model(model_switch_reason):
                                break
                            model_failed = True
                            break

                        print(
                            f"[GROQ ROTATOR] Key #{groq_rotator.current_key_index + 1} "
                            f"failed: {error_message[:200]}"
                        )
                        groq_rotator.mark_failed(groq_rotator.current_key_index)
                        last_error = api_error
                        if not groq_rotator.advance():
                            break
                        tried_keys += 1

                if raw_reply:
                    break
                if model_failed:
                    continue
                break

            if not raw_reply:
                zesty_logger.log_error(
                    component="Groq Provider",
                    reason="All keys exhausted or all models failed",
                    recovery="Temporary unavailability",
                )
                return (
                    "System array disruption. Local neural core is temporarily unavailable.",
                    "chat",
                )

            api_end = time.perf_counter()
            api_request_ms = (api_end - api_start) * 1000
            first_token_ms = api_request_ms
            generation_ms = (api_end - api_start) * 1000
            overall_ms = (api_end - llm_start) * 1000

            zesty_logger.log_model(
                provider="Groq",
                model=groq_model_router.current_model,
                key_index=groq_rotator.current_key_index,
                retry_count=tried_keys,
                fallback_used=groq_model_router.current_model_index > start_model_index,
                rotation_triggered=tried_keys > 0,
            )

            print(f"[⏱ LLM TIME] {overall_ms:.2f} ms")

            print("\n" + "=" * 70)
            print("🧠 ZESTY RAW REPLY")
            print("-" * 70)
            print(raw_reply)
            print("=" * 70 + "\n")

            panel_target = "chat"

            panel_match = re.search(
                r'\[TARGET_PANEL:\s*([A-Za-z_]+)\]',
                raw_reply,
            )

            if panel_match:
                panel_target = panel_match.group(1)
                raw_reply = re.sub(
                    r'\[TARGET_PANEL:\s*[A-Za-z_]+\]',
                    '',
                    raw_reply,
                ).strip()

            if raw_reply:
                raw_for_debug = raw_reply
                raw_reply = self._sanitize_response(raw_reply)
                after_sanitize = raw_reply
                raw_reply = self._enforce_response_execution(
                    raw_reply, execution_flags, lang_hint, user_prompt=user_prompt
                )
                if DEBUG_COGNITION and self._cognition_trace is not None:
                    self._cognition_trace.set_model(
                        provider="Groq",
                        model=groq_model_router.current_model,
                        api_key_index=groq_rotator.current_key_index,
                        temperature=0.55,
                    )
                    self._cognition_trace.set_outputs(
                        raw_model_output=raw_for_debug,
                        after_sanitize=after_sanitize,
                        after_enforce=raw_reply,
                        execution_flags=execution_flags,
                    )
                    self._cognition_trace.emit()
                    self._cognition_trace = None

            zesty_logger.log_response(
                reply=raw_reply,
                token_count=len(raw_reply.split()) if raw_reply else 0,
            )

            if session_id:
                self.saved_profiles.consume_proactive_nudge(session_id)

            return raw_reply, panel_target

        except Exception as e:

            import traceback
            print(f"[⚠️ RUNTIME ERROR]: {e}")
            traceback.print_exc()

            return (
                "System array disruption. Local neural core is temporarily unavailable.",
                "chat",
            )



zesty_os = ZestyCommercialOS()

zesty_logger.configure(
    groq_keys=len(getattr(groq_rotator, "keys", [])),
    groq_key_index=getattr(groq_rotator, "current_key_index", None),
    groq_model=groq_model_router.current_model if groq_model_router.AVAILABLE_MODELS else GROQ_MODEL,
    groq_available_models=groq_model_router.AVAILABLE_MODELS,
    groq_fallback_model=groq_model_router.fallback_model,
    persona_loaded=True,
    system_prompt_len=len(zesty_system_prompt),
)
zesty_logger.start()
#endregion

# =====================================================================
#region 🌐 4. NETWORK ROUTES & ENDPOINTS
# =====================================================================
@app.route("/")
def index():
    try:
        return send_from_directory("templates", "index.html")
    except Exception as e:
        return f"Zesty OS Cockpit Error: {str(e)}"


@app.route("/assets/<path:filename>")
def zesty_assets(filename):
    return send_from_directory("templates", filename)


@app.route("/api/saved-profiles", methods=["GET"])
def api_saved_profiles():
    try:
        profiles = zesty_os.saved_profiles.list_profiles()
        return jsonify(zesty_os.saved_profiles.build_vault_payload(profiles))
    except Exception:
        return jsonify({"total": 0, "profiles": [], "folders": {}}), 500


@app.route("/api/presence/status", methods=["GET"])
def api_presence_status():
    try:
        return jsonify(zesty_os.presence_manager.to_api_payload())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/presence/wake", methods=["POST"])
def api_presence_wake():
    try:
        snap = zesty_os.presence_manager.handle_api_wake()
        return jsonify(snap.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/presence/simulate", methods=["POST"])
def api_presence_simulate():
    try:
        from presence.commands import SimulateAction, SimulateCommand, parse_simulate_command

        data = request.json or {}
        action = str(data.get("action") or "").strip().lower()
        name = str(data.get("name") or "").strip()
        if not action:
            text = str(data.get("text") or "").strip()
            cmd = parse_simulate_command(text) if text else None
        else:
            try:
                cmd = SimulateCommand(action=SimulateAction(action), name=name)
            except ValueError:
                cmd = None
        if not cmd:
            return jsonify({"error": "Invalid action. Use wake, sleep, chief, known, unknown, privacy_hold, reset, status."}), 400
        snap, reply = zesty_os.presence_manager.run_simulate(cmd)
        return jsonify({"reply": reply, "presence": zesty_os.presence_manager.to_api_payload()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/ask_hermes", methods=["POST"])
def ask_hermes_endpoint():
    print(f"\n[DEBUG BACKEND]: /ask_hermes endpoint hit - Connection VERIFIED from frontend")
    try:
        return _ask_hermes_impl()
    except Exception as e:
        import traceback
        print(f"[FATAL ERROR in ask_hermes_endpoint]: {e}")
        traceback.print_exc()
        return jsonify({
            "voice_text": "System array disruption. Local neural core is temporarily unavailable.",
            "dynamic_html": "<div class='hermes-dynamic-content'>System array disruption.</div>",
            "open_panel": "chat"
        }), 500

def _ask_hermes_impl():
    request_start = time.perf_counter()
    data = request.json or {}
    print(f"[DEBUG BACKEND]: Request data received -> {data}")
    
    raw_input = str(data.get("user_input", ""))
    cleaned_input = zesty_os.clean_phonetics_layer(raw_input)
    lower_input = cleaned_input.lower()

    session_id = str(data.get("session_id") or "").strip() or "zesty-primary-session"
    conversation_manager.ensure_session(session_id)
    working_memory_engine.ensure_session(session_id)
    log_session_id = zesty_logger.next_session_id()
    lang_hint = zesty_os.resolve_session_language(session_id, cleaned_input)
    if DEBUG_COGNITION:
        zesty_os._cognition_trace = CognitionDebugTrace()
        zesty_os._cognition_trace.set_request(
            user_message=cleaned_input,
            detected_language=zesty_os.detect_language(cleaned_input),
            session_language=lang_hint,
            execution_flags=zesty_os._parse_execution_flags(cleaned_input),
        )
    else:
        zesty_os._cognition_trace = None
    zesty_logger.log_request(log_session_id, raw_input, lang_hint)

    if any(kw in lower_input for kw in ["stop", "ruko", "cancel"]):
        stop_tts_playback()
        return jsonify({"voice_text": "Stopped", "dynamic_html": "Playback stopped.", "open_panel": "CLOSE"})

    if any(kw in lower_input for kw in ["daddy", "home", "duty", "जैस्री"]) and not zesty_os.boss_mode_active:
        zesty_os.boss_mode_active = True
        greeting = zesty_os.build_dynamic_mood_greeting(raw_input, lang_hint=lang_hint)
        zesty_os.speak_text_edge_seamless(greeting, lang_hint)
        return jsonify({"voice_text": greeting, "dynamic_html": greeting, "open_panel": "chat"})

    is_os_cmd = False
    output_intel = ""

    owner_self_query = zesty_os.owner_profile.is_self_query(cleaned_input)
    from presence.models import PresenceState

    presence_state = zesty_os.presence_manager.snapshot.state
    presence_restricted = presence_state in (
        PresenceState.UNKNOWN_RESTRICTED,
        PresenceState.PRIVACY_HOLD,
    )
    will_probe = zesty_os._will_run_social_probe(
        cleaned_input,
        owner_self_query=owner_self_query,
        presence_restricted=presence_restricted,
    )

    if not will_probe:
        is_os_cmd, output_intel = zesty_os.execute_os_command_or_research(cleaned_input)
    if is_os_cmd:
        zesty_os.speak_text_edge_seamless(output_intel, "english")
        return jsonify({"voice_text": output_intel, "dynamic_html": output_intel, "open_panel": "chat"})

    presence_response = zesty_os.handle_presence_command(cleaned_input)
    if presence_response:
        zesty_os.speak_text_edge_seamless(presence_response["voice_text"], lang_hint)
        zesty_os._record_profile_cmd_in_history(
            session_id, cleaned_input, presence_response["voice_text"]
        )
        return jsonify(presence_response)

    if zesty_os.saved_profiles.parse_command(cleaned_input) and not zesty_os.presence_manager.allows_vault_commands():
        denial = zesty_os.presence_manager.vault_denial_reply()
        zesty_os.speak_text_edge_seamless(denial, lang_hint)
        zesty_os._record_profile_cmd_in_history(session_id, cleaned_input, denial)
        return jsonify({
            "voice_text": denial,
            "dynamic_html": f"<div class='hermes-dynamic-content'>{denial}</div>",
            "open_panel": "chat",
            "presence": zesty_os.presence_manager.to_api_payload(),
        })

    profile_cmd = zesty_os.saved_profiles.handle_command(
        cleaned_input,
        session_id,
        deep_probe_engine=zesty_os.deep_probe_engine,
    )
    if profile_cmd.handled:
        zesty_os.speak_text_edge_seamless(profile_cmd.voice_text, lang_hint)
        zesty_os._record_profile_cmd_in_history(session_id, cleaned_input, profile_cmd.voice_text)
        if profile_cmd.deep_probe:
            zesty_os.saved_profiles.set_last_probe(session_id, profile_cmd.deep_probe)
        response_payload = {
            "voice_text": profile_cmd.voice_text,
            "dynamic_html": f"<div class='hermes-dynamic-content'>{profile_cmd.voice_text}</div>",
            "open_panel": profile_cmd.open_panel,
        }
        if profile_cmd.target_image_url:
            response_payload["target_image_url"] = profile_cmd.target_image_url
        if profile_cmd.deep_probe:
            response_payload["deep_probe"] = profile_cmd.deep_probe
        if profile_cmd.social_profile:
            response_payload["social_profile"] = profile_cmd.social_profile
        if profile_cmd.saved_profiles_list:
            response_payload["saved_profiles"] = profile_cmd.saved_profiles_list
        if profile_cmd.ui_mode:
            response_payload["ui_mode"] = profile_cmd.ui_mode
        if profile_cmd.vault_payload:
            response_payload["vault"] = profile_cmd.vault_payload
        if profile_cmd.lookup_name:
            response_payload["lookup_name"] = profile_cmd.lookup_name
            response_payload["lookup_found"] = profile_cmd.lookup_found
        if profile_cmd.selected_profile_id:
            response_payload["selected_profile_id"] = profile_cmd.selected_profile_id
        if profile_cmd.profile_action:
            response_payload["profile_action"] = profile_cmd.profile_action
        return jsonify(response_payload)

    deep_probe_payload = None
    target_image_url = None
    force_panel = None
    skip_llm = False
    probe_mode = False

    if owner_self_query:
        if not zesty_os.presence_manager.allows_chief_identity():
            denial = zesty_os.presence_manager.chief_identity_denial_reply()
            zesty_os.speak_text_edge_seamless(denial, lang_hint)
            zesty_os._record_profile_cmd_in_history(session_id, cleaned_input, denial)
            return jsonify({
                "voice_text": denial,
                "dynamic_html": f"<div class='hermes-dynamic-content'>{denial}</div>",
                "open_panel": "chat",
                "presence": zesty_os.presence_manager.to_api_payload(),
            })
        deep_probe_payload = zesty_os.owner_profile.to_social_payload(
            deep_probe_engine=zesty_os.deep_probe_engine,
        )
        force_panel = "panelSocial"
        probe_mode = True
        skip_llm = is_pure_data_probe_query(cleaned_input)
        target_image_url = deep_probe_payload.get("profile_image_url")
        output_intel = (
            "[CHIEF IDENTITY — Owner profile, not web search]\n\n"
            + (deep_probe_payload.get("facts_text") or "")
        )
        zesty_os.saved_profiles.set_last_probe(session_id, deep_probe_payload)
        zesty_os.saved_profiles.record_session_action(
            session_id,
            "chief_identity",
            deep_probe_payload.get("name") or "Chief",
        )
    elif will_probe and not presence_restricted:
        saved_match = zesty_os.saved_profiles.find_match(cleaned_input)
        if saved_match and not zesty_os.presence_manager.allows_probe_context(saved_match):
            saved_match = None
        probe_mode = True
        skip_llm = is_pure_data_probe_query(cleaned_input)
        if saved_match:
            deep_probe_payload = saved_match
            force_panel = "panelSocial"
            target_image_url = saved_match.get("profile_image_url")
            probe_facts = (saved_match.get("facts_text") or saved_match.get("panel_text") or "").strip()
            if probe_facts:
                output_intel = f"[SAVED PROFILE — from memory, not live search]\n\n{probe_facts}"
            zesty_os.saved_profiles.set_last_probe(session_id, saved_match)
            zesty_os.saved_profiles.record_session_action(
                session_id,
                "saved_profile_recall",
                saved_match.get("name") or "",
            )
        else:
            deep_probe_payload = zesty_os.deep_probe_engine.probe(cleaned_input)
            if deep_probe_payload:
                force_panel = "panelSocial"
                target_image_url = deep_probe_payload.get("profile_image_url") or None
                probe_facts = (deep_probe_payload.get("facts_text") or "").strip()
                if probe_facts:
                    output_intel = probe_facts
                zesty_os.saved_profiles.set_last_probe(session_id, deep_probe_payload)
                zesty_os.saved_profiles.record_session_action(
                    session_id,
                    "deep_probe",
                    deep_probe_payload.get("name") or "",
                    proactive_nudge=(
                        "If Chief asks a follow-up about this person, answer from the probe — "
                        "one brief connective phrase is enough."
                    ),
                )

    zesty_os._update_session_continuity(
        session_id,
        cleaned_input,
        deep_probe_payload=deep_probe_payload,
    )

    local_context = ""
    if not will_probe:
        local_context = zesty_os.query_local_chroma_database(cleaned_input)

    conversation_manager.add_message(session_id, "user", cleaned_input)

    include_chief = owner_self_query or zesty_os.owner_profile.is_chief_reference(cleaned_input)

    if skip_llm and deep_probe_payload:
        reply_text = format_probe_voice_summary(
            deep_probe_payload, owner_self=owner_self_query
        )
        target_panel = force_panel or "panelSocial"
        print("[PROBE FAST PATH] Skipping LLM — using structured probe data", flush=True)
    else:
        reply_text, target_panel = zesty_os.call_llm(
            cleaned_input,
            local_context,
            output_intel,
            session_id,
            lang_hint=lang_hint,
            owner_self_query=owner_self_query,
            probe_mode=probe_mode,
            include_chief_identity=include_chief,
        )

    if force_panel:
        target_panel = force_panel

    # Add assistant response to conversation history
    conversation_manager.add_message(session_id, "assistant", reply_text)

    print(f"[TARGET PANEL] {target_panel}")
    print(f"[FINAL REPLY] {reply_text}")
    if deep_probe_payload:
        print(f"[DEEP PROBE] platform={deep_probe_payload.get('platform')} image={bool(target_image_url)}")
    
    if not target_image_url and deep_probe_payload:
        target_image_url = deep_probe_payload.get("profile_image_url")

    zesty_os.speak_text_edge_seamless(
        reply_text,
        lang_hint,
        social_probe=bool(deep_probe_payload or force_panel == "panelSocial"),
    )

    zesty_logger.record_latency((time.perf_counter() - request_start) * 1000)

    response_payload = {
        "voice_text": reply_text,
        "dynamic_html": f"<div class='hermes-dynamic-content'>{reply_text}</div>",
        "open_panel": target_panel,
        "presence": zesty_os.presence_manager.to_api_payload(),
    }
    if target_image_url:
        response_payload["target_image_url"] = target_image_url
    if deep_probe_payload:
        response_payload["deep_probe"] = deep_probe_payload
        response_payload["social_profile"] = zesty_os.saved_profiles.profile_to_social_payload(
            deep_probe_payload
        )
        response_payload["response_phase"] = "fast" if skip_llm else "summary"

    return jsonify(response_payload)
#endregion

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)