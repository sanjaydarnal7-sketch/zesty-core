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
from tts_router import TTSRouter
from zesty_runtime_logger import zesty_logger
from conversation_manager.manager import ConversationManager
from conversation.working_memory import WorkingMemoryEngine
from cognition_debug import DEBUG_COGNITION, CognitionDebugTrace, memory_reject_reason
from deep_probe_engine import DeepProbeEngine
from owner_profile import OwnerProfile
from saved_profiles import SavedProfilesStore
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from dotenv import load_dotenv

load_dotenv()

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

tts_router = TTSRouter()

DB_DIR = "zesty_knowledge_base"
chroma_client = chromadb.PersistentClient(path=DB_DIR)
JOURNAL_FILE = "boss_personal_journal.json"
CONVERSATION_HISTORY = []

conversation_manager = ConversationManager()
working_memory_engine = WorkingMemoryEngine()

class ZestyCloudEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> any: # type: ignore
        try:
            url = "https://feature-extraction.hf.space/embed"
            res = requests.post(url, json={"inputs": input}, timeout=3.0)
            if res.status_code == 200: return res.json()
        except Exception: pass
        return [[0.0] * 384 for _ in input]

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
        self._owner_update_asked_sessions: set[str] = set()

        self.cleanup_audio()

    def cleanup_audio(self):
        try:
            subprocess.run(["pkill", "afplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists("zesty_reply.mp3"): os.remove("zesty_reply.mp3")
        except Exception: pass

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
        """Sticky thread language — switch only when the user clearly switches."""
        explicit = self._detect_explicit_language_switch(text)
        if explicit:
            self._session_lang[session_id] = explicit
            return explicit

        detected = self.detect_language(text)
        prev = self._session_lang.get(session_id)
        if prev is None:
            self._session_lang[session_id] = detected
            return detected
        if detected == prev:
            return prev

        # Hindi thread does not drift to English on short English fragments.
        if prev == "hindi" and detected == "english":
            return prev

        if self._user_clearly_switched_language(text, detected):
            self._session_lang[session_id] = detected
            return detected
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
        # Greeting / service templates
        if re.match(r"^(hi|hello|hey|namaste)\b", lower) and ("?" in raw or "help" in lower):
            return True
        return False

    def _format_factual_memories(self, documents: list) -> str:
        """Keep knowledge only — projects, people, preferences, facts."""
        facts: list[str] = []
        seen: set[str] = set()
        for doc in documents:
            if not doc or not str(doc).strip():
                continue
            text = str(doc).strip()
            if self._is_assistant_style_memory(text):
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            facts.append(text)
            if len(facts) >= 3:
                break
        if not facts:
            return ""
        return "\n".join(f"- {fact}" for fact in facts)

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
                factual = self._format_factual_memories(docs)
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
                if distances:
                    memory_ranking = float(distances[0])
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

    def speak_text_edge_seamless(self, text_to_speak: str, current_lang: str):
        tts_start = time.perf_counter()
        tts_lang = "en" if current_lang == "english" else "hi"
        tts_router.speak_text(text_to_speak, tts_lang)
        tts_ms = (time.perf_counter() - tts_start) * 1000
        voice_name = "Edge TTS"
        if getattr(tts_router, "_elevenlabs_available", False):
            voice_name = "ElevenLabs"
        zesty_logger.log_voice(
            voice_name=voice_name,
            audio_generated=bool(text_to_speak.strip()),
            duration_ms=tts_ms,
        )

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

        # hindi — same minimal lock shape as English; one parity line only
        return (
            "## Language Lock (this turn)\n\n"
            "Reply in Hindi (Devanagari) only for this turn. "
            "Stay in Hindi for this thread unless the user's latest message clearly switched language. "
            "Never translate unless asked. Never force slang or honorifics the user did not use.\n\n"
            "Write Hindi exactly as the English version would sound if spoken naturally by the same person. "
            "Do not increase formality, politeness, explanation depth, or sentence length merely because the language is Hindi."
        )

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
    ) -> str:
        """Build the OpenPersona system prompt with runtime state, research, memory, and history."""
        system_prompt = zesty_persona.build_system_prompt(include_faculties=include_faculties)

        runtime_block = zesty_persona.format_runtime_context()
        if runtime_block:
            system_prompt += "\n\n" + runtime_block

        if self.owner_profile.should_inject():
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
                    system_prompt += (
                        "\n\n## Conversation Continuity\n\n"
                        "Semantic state only — intent, facts, decisions, topic. "
                        "Do not imitate prior wording, tone, slang, or service phrasing.\n"
                        + "\n".join(continuity_parts)
                    )
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
        subprocess.run(["pkill", "afplay"])
        return jsonify({"voice_text": "Stopped", "dynamic_html": "Playback stopped.", "open_panel": "CLOSE"})

    if any(kw in lower_input for kw in ["daddy", "home", "duty", "जैस्री"]) and not zesty_os.boss_mode_active:
        zesty_os.boss_mode_active = True
        greeting = zesty_os.build_dynamic_mood_greeting(raw_input, lang_hint=lang_hint)
        zesty_os.speak_text_edge_seamless(greeting, lang_hint)
        return jsonify({"voice_text": greeting, "dynamic_html": greeting, "open_panel": "chat"})

    is_os_cmd, output_intel = zesty_os.execute_os_command_or_research(cleaned_input)
    if is_os_cmd:
        zesty_os.speak_text_edge_seamless(output_intel, "english")
        return jsonify({"voice_text": output_intel, "dynamic_html": output_intel, "open_panel": "chat"})

    profile_cmd = zesty_os.saved_profiles.handle_command(
        cleaned_input,
        session_id,
        deep_probe_engine=zesty_os.deep_probe_engine,
    )
    if profile_cmd.handled:
        zesty_os.speak_text_edge_seamless(profile_cmd.voice_text, lang_hint)
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

    owner_self_query = zesty_os.owner_profile.is_self_query(cleaned_input)
    deep_probe_payload = None
    target_image_url = None
    force_panel = None

    if owner_self_query:
        deep_probe_payload = zesty_os.owner_profile.to_social_payload()
        force_panel = "panelSocial"
        output_intel = (
            "[CHIEF IDENTITY — Owner profile, not web search]\n\n"
            + (deep_probe_payload.get("facts_text") or "")
        )
        zesty_os.saved_profiles.set_last_probe(session_id, deep_probe_payload)
    elif zesty_os.deep_probe_engine.should_probe(cleaned_input):
        saved_match = zesty_os.saved_profiles.find_match(cleaned_input)
        if saved_match:
            deep_probe_payload = saved_match
            force_panel = "panelSocial"
            target_image_url = saved_match.get("profile_image_url")
            probe_facts = (saved_match.get("facts_text") or saved_match.get("panel_text") or "").strip()
            if probe_facts:
                output_intel = f"[SAVED PROFILE — from memory, not live search]\n\n{probe_facts}"
            zesty_os.saved_profiles.set_last_probe(session_id, saved_match)
        else:
            deep_probe_payload = zesty_os.deep_probe_engine.probe(cleaned_input)
            if deep_probe_payload:
                force_panel = "panelSocial"
                target_image_url = deep_probe_payload.get("profile_image_url") or None
                probe_facts = (deep_probe_payload.get("facts_text") or "").strip()
                if probe_facts:
                    if output_intel and output_intel.strip() and output_intel != ResearchService.NO_USABLE_FACTS:
                        output_intel = f"{output_intel.strip()}\n\n{probe_facts}"
                    else:
                        output_intel = probe_facts
                zesty_os.saved_profiles.set_last_probe(session_id, deep_probe_payload)

    local_context = zesty_os.query_local_chroma_database(cleaned_input)

    # Track active topic from current user intent (semantic continuity)
    topic_hint = cleaned_input.strip()
    if len(topic_hint) > 80:
        topic_hint = topic_hint[:80].rsplit(" ", 1)[0]
    try:
        conversation_manager.set_active_topic(session_id, topic_hint)
        conversation_manager.update_topic_structured(session_id, topic_hint)
    except Exception:
        pass

    # Add user message to conversation history
    conversation_manager.add_message(session_id, "user", cleaned_input)

    reply_text, target_panel = zesty_os.call_llm(
        cleaned_input,
        local_context,
        output_intel,
        session_id,
        lang_hint=lang_hint,
        owner_self_query=owner_self_query,
    )

    if force_panel:
        target_panel = force_panel

    # Add assistant response to conversation history
    conversation_manager.add_message(session_id, "assistant", reply_text)

    print(f"[TARGET PANEL] {target_panel}")
    print(f"[FINAL REPLY] {reply_text}")
    if deep_probe_payload:
        print(f"[DEEP PROBE] platform={deep_probe_payload.get('platform')} image={bool(target_image_url)}")
    
    zesty_os.speak_text_edge_seamless(reply_text, lang_hint)

    response_payload = {
        "voice_text": reply_text,
        "dynamic_html": f"<div class='hermes-dynamic-content'>{reply_text}</div>",
        "open_panel": target_panel,
    }
    if target_image_url:
        response_payload["target_image_url"] = target_image_url
    if deep_probe_payload:
        response_payload["deep_probe"] = deep_probe_payload
        response_payload["social_profile"] = zesty_os.saved_profiles.profile_to_social_payload(
            deep_probe_payload
        )

    return jsonify(response_payload)
#endregion

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)