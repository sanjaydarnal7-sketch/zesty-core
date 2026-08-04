import os
import sys
import time
import threading
import platform
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from datetime import datetime
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

COLOR_SUPPORT = sys.stdout.isatty() and platform.system() != "Windows"

COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "cyan": "\033[36m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "magenta": "\033[35m",
    "blue": "\033[34m",
    "white": "\033[37m",
    "grey": "\033[90m",
}

STATUS_COLORS = {
    "ok": "green",
    "warn": "yellow",
    "error": "red",
    "info": "cyan",
    "muted": "grey",
}


def _color(text: str, color: str) -> str:
    if not COLOR_SUPPORT:
        return text
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"


def _print_divider(char: str = "-", length: int = 72, color: str = "cyan"):
    print(_color(char * length, color))


def _print_header(title: str):
    _print_divider("=", color="cyan")
    print(_color(f"ZESTY OS RUNTIME - {title}", "bold"))
    _print_divider("=", color="cyan")


@dataclass
class RequestMetrics:
    session_id: str = ""
    start_time: float = field(default_factory=time.perf_counter)
    memory_retrieval_ms: float = 0.0
    prompt_build_ms: float = 0.0
    api_request_ms: float = 0.0
    time_to_first_token_ms: float = 0.0
    generation_ms: float = 0.0
    total_response_ms: float = 0.0
    tts_ms: float = 0.0
    overall_ms: float = 0.0
    provider: str = ""
    model: str = ""
    key_index: Optional[int] = None
    retry_count: int = 0
    fallback_used: bool = False
    rotation_triggered: bool = False
    reply_length: int = 0
    token_count: Optional[int] = None
    voice_name: str = ""
    audio_generated: bool = False
    audio_duration_ms: float = 0.0
    memories_retrieved: int = 0
    memory_ids: list = field(default_factory=list)
    memory_ranking: float = 0.0
    error: Optional[str] = None
    error_component: str = ""
    recovery: str = ""


class ZestyRuntimeLogger:
    def __init__(self):
        self.debug_mode = os.environ.get("ZESTY_DEBUG", "true").lower() == "true"
        self.request_count = 0
        self.session_counter = 0
        self.start_time = time.perf_counter()
        self.recent_latencies = deque(maxlen=20)
        self.active_sessions = {}
        self.conversation_stats = {
            "total_messages": 0,
            "current_session_turns": 0,
            "avg_reply_length": 0.0,
            "avg_latency": 0.0,
            "avg_memory_recall": 0.0,
        }
        self._lock = threading.Lock()
        self._health_thread = None
        self._health_stop = threading.Event()

    @property
    def uptime(self) -> float:
        return time.perf_counter() - self.start_time

    def start(self):
        self._print_startup_summary()
        self._start_health_monitor()

    def stop(self):
        self._health_stop.set()
        if self._health_thread and self._health_thread.is_alive():
            self._health_thread.join(timeout=1)

    def next_session_id(self) -> str:
        with self._lock:
            self.session_counter += 1
            return f"SES-{self.session_counter:04d}"

    # ----------------------------
    # 1. Startup Summary
    # ----------------------------
    def _print_startup_summary(self):
        groq_keys = getattr(self, "_groq_keys", 0)
        key_index = getattr(self, "_groq_key_index", None)
        groq_model = getattr(self, "_groq_model", "unknown")
        persona_loaded = getattr(self, "_persona_loaded", False)
        system_prompt_len = getattr(self, "_system_prompt_len", 0)

        _print_header("STARTUP SUMMARY")
        print(
            _color("✓ Groq API Keys Loaded", "green"),
            f": {groq_keys}" if groq_keys > 0 else _color(": 0", "red"),
        )
        print(_color("✓ Active Groq Model", "green"), f": {groq_model}")
        if key_index is not None:
            print(_color("✓ Current Key Index", "green"), f": #{key_index + 1}")
        print(_color("✓ ChromaDB Status", "green"), ": READY")
        print(_color("✓ Memory Status", "green"), ": READY")
        print(_color("✓ OpenPersona Status", "green"), ": READY" if persona_loaded else _color(": NOT LOADED", "red"))
        if system_prompt_len:
            print(
                _color("✓ Conversation DNA Loaded", "green"),
                f": {system_prompt_len} chars",
            )
        print(_color("✓ Flask Status", "green"), ": READY")
        print(_color("✓ Active Port", "green"), ": 5001")
        print(_color("✓ Debug Mode", "green"), f": {self.debug_mode}")
        print(_color("✓ Python Version", "green"), f": {platform.python_version()}")
        _print_divider()

    def configure(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, f"_{key}", value)

    # ----------------------------
    # 2. Incoming User Request
    # ----------------------------
    def log_request(self, session_id: str, user_message: str, language: str = "unknown"):
        self.request_count += 1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.active_sessions[session_id] = {
            "last_seen": time.time(),
            "turns": self.conversation_stats["current_session_turns"],
        }

        _print_divider()
        print(_color("REQUEST", "bold"))
        print(f"Timestamp : {now}")
        print(f"Session   : {session_id}")
        print(f"Message   : {user_message}")
        print(f"Length    : {len(user_message)} chars")
        print(f"Language  : {language}")
        _print_divider()

    # ----------------------------
    # 3. Memory
    # ----------------------------
    def log_memory(
        self,
        working_memory: str,
        long_term_memories: int,
        memory_ids: list,
        ranking_score: float,
        retrieval_time_ms: float,
    ):
        print(_color("MEMORY", "bold"))
        print(f"Working Memory        : {working_memory[:120]}{'...' if len(working_memory) > 120 else ''}")
        print(f"Long-Term Memories    : {long_term_memories}")
        print(f"Memories Retrieved    : {len(memory_ids)}")
        if memory_ids:
            print(f"Memory IDs            : {', '.join(memory_ids[:5])}{'...' if len(memory_ids) > 5 else ''}")
        print(f"Memory Ranking Score  : {ranking_score:.4f}")
        print(f"Retrieval Time        : {retrieval_time_ms:.1f} ms")
        _print_divider()

    # ----------------------------
    # 4. Prompt Assembly
    # ----------------------------
    def log_prompt(
        self,
        persona_loaded: bool,
        conversation_dna_loaded: bool,
        history_tokens: int,
        memory_tokens: int,
        final_tokens: int,
    ):
        print(_color("PROMPT ASSEMBLY", "bold"))
        print(f"Persona Loaded              : {'YES' if persona_loaded else 'NO'}")
        print(f"Conversation DNA Loaded     : {'YES' if conversation_dna_loaded else 'NO'}")
        print(f"History Tokens              : {history_tokens}")
        print(f"Retrieved Memory Tokens     : {memory_tokens}")
        print(f"Final Prompt Tokens         : {final_tokens}")
        _print_divider()

    def record_latency(self, latency_ms: float) -> None:
        with self._lock:
            self.recent_latencies.append(latency_ms)

    def log_final_prompt(
        self,
        system_prompt: str,
        conversation_dna_text: str,
        persona_text: str,
        memory_text: str,
        history_text: str,
        user_message: str,
        anti_meta_text: str = "",
    ):
        sections = [("SYSTEM", system_prompt)]
        if memory_text:
            sections.append(("MEMORY", memory_text))
        if history_text:
            sections.append(("HISTORY", history_text))
        sections.append(("USER", user_message))

        dna_in_system = bool(
            conversation_dna_text and conversation_dna_text.strip() in system_prompt
        )
        persona_in_system = bool(persona_text and persona_text.strip() in system_prompt)
        dna_dup = (
            conversation_dna_text
            and system_prompt.count(conversation_dna_text.strip()[:120]) > 1
        )
        persona_dup = (
            persona_text and system_prompt.count(persona_text.strip()[:120]) > 1
        )

        print(_color("FINAL PROMPT STRUCTURE", "bold"))
        print(f"System Prompt Length        : {len(system_prompt)}")
        print(f"Conversation DNA (in SYSTEM): {'YES' if dna_in_system else 'NO'}")
        print(f"Persona injection (in SYS)  : {'YES' if persona_in_system else 'NO'}")
        if dna_dup or persona_dup:
            print(_color("WARNING: Soul content duplicated in SYSTEM block", "yellow"))
        print(f"Retrieved Memory Length     : {len(memory_text)}")
        print(f"History Length              : {len(history_text)}")
        print(f"User Message Length         : {len(user_message)}")
        print(
            f"Final Prompt Length         : "
            f"{len(system_prompt) + len(memory_text) + len(history_text) + len(user_message)}"
        )
        _print_divider()

        for title, text in sections:
            print(_color(f"========== {title} ==========", "bold"))
            print(text)
            print()

        self._analyze_prompt(system_prompt, conversation_dna_text, persona_text, user_message)

    def _analyze_prompt(
        self,
        system_prompt: str,
        conversation_dna_text: str,
        persona_text: str,
        user_message: str,
    ):
        print(_color("PROMPT ANALYSIS", "bold"))
        issues = []
        if conversation_dna_text and system_prompt.count(conversation_dna_text) != 1:
            issues.append("Conversation DNA appears more than once or is missing")
        if persona_text and system_prompt.count(persona_text) != 1:
            issues.append("Persona appears more than once or is missing")
        lowers = system_prompt.lower()
        if "you are a helpful assistant" in lowers:
            issues.append("Generic assistant prompt detected")
        if lowers.count("you are zesty") > 2:
            issues.append("Duplicate persona identity detected")
        # Check for service-framing phrases that might be injected by the runtime
        # Skip phrases that appear in "forbidden" or "avoid" sections of the persona
        runtime_service_framing = [
            "how can i help you today",
            "happy to assist",
            "is there anything else i can help you with",
            "i'd be happy to help",
            "i understand your concern",
        ]
        for phrase in runtime_service_framing:
            if phrase in lowers:
                # Check if this phrase appears in a forbidden/avoid context
                idx = lowers.find(phrase)
                context_before = lowers[max(0, idx-300):idx]
                skip_words = ["forbidden", "avoid", "never", "don't", "do not", "skip", "no service framing"]
                if any(word in context_before for word in skip_words):
                    continue  # This is in a forbidden/avoid section, not an actual instruction
                issues.append(f"Service-framing phrase detected: '{phrase}'")
        if issues:
            print("Issues detected:")
            for issue in issues:
                print(f"- {issue}")
        else:
            print("No prompt structure issues detected.")

        lower_user = user_message.lower()
        if ("what's up" in lower_user or "whats up" in lower_user) and ("yaar" in system_prompt.lower() or "buddy" in system_prompt.lower()):
            print()
            print(_color("FILLER TRACE", "yellow"))
            print("The final prompt includes buddy-language instructions in the persona/conversation DNA.")
            print("If the model replies with 'yaar', the source is the loaded Conversation DNA / persona,")
            print("not a generic assistant template.")
        _print_divider()

    # ----------------------------
    # 5. AI Provider
    # ----------------------------
    def log_model(
        self,
        provider: str,
        model: str,
        key_index: Optional[int],
        retry_count: int,
        fallback_used: bool,
        rotation_triggered: bool,
    ):
        print(_color("MODEL", "bold"))
        print(f"Provider              : {provider}")
        print(f"Model Name            : {model}")
        print(f"API Key Index Used    : {'#' + str(key_index) if key_index is not None else 'N/A'}")
        print(f"Retry Count           : {retry_count}")
        print(f"Fallback Used         : {'YES' if fallback_used else 'NO'}")
        print(f"Groq Rotation Triggered: {'YES' if rotation_triggered else 'NO'}")
        _print_divider()

    # ----------------------------
    # 6. Timing
    # ----------------------------
    def log_timing(self, metrics: RequestMetrics):
        print(_color("LATENCY", "bold"))
        print(f"Memory Retrieval      : {metrics.memory_retrieval_ms:>6.1f} ms")
        print(f"Prompt Build          : {metrics.prompt_build_ms:>6.1f} ms")
        print(f"API Request           : {metrics.api_request_ms:>6.1f} ms")
        print(f"Time To First Token   : {metrics.time_to_first_token_ms:>6.1f} ms")
        print(f"Generation            : {metrics.generation_ms:>6.1f} ms")
        print(f"TTS                   : {metrics.tts_ms:>6.1f} ms")
        print(f"TOTAL                 : {metrics.overall_ms:>6.1f} ms")
        _print_divider()

    # ----------------------------
    # 7. Generated Response
    # ----------------------------
    def log_response(self, reply: str, token_count: Optional[int] = None):
        self.reply_length = len(reply)
        self.reply_token_count = token_count
        print(_color("ZESTY", "bold"))
        print(reply)
        print()
        print(f"Reply Length          : {len(reply)} chars")
        if token_count:
            print(f"Token Count           : {token_count}")
        _print_divider()

    # ----------------------------
    # 8. Voice
    # ----------------------------
    def log_voice(self, voice_name: str, audio_generated: bool, duration_ms: float):
        print(_color("VOICE", "bold"))
        print(f"Voice Name            : {voice_name}")
        print(f"Audio Generated       : {'YES' if audio_generated else 'NO'}")
        print(f"Audio Duration        : {duration_ms:.1f} ms")
        _print_divider()

    # ----------------------------
    # 9. Errors
    # ----------------------------
    def log_error(self, component: str, reason: str, recovery: str):
        print(_color("ERROR", "red"))
        print(f"Component     : {component}")
        print(f"Reason        : {reason}")
        print(f"Recovery      : {recovery}")
        _print_divider()

    # ----------------------------
    # 10. Runtime Health
    # ----------------------------
    def _start_health_monitor(self):
        def monitor():
            while not self._health_stop.is_set():
                time.sleep(30)
                self._print_runtime_health()

        self._health_thread = threading.Thread(target=monitor, daemon=True)
        self._health_thread.start()

    def _print_runtime_health(self):
        try:
            process = psutil.Process()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
        except Exception:
            cpu_percent = 0.0
            memory_mb = 0.0

        avg_latency = (
            sum(self.recent_latencies) / len(self.recent_latencies)
            if self.recent_latencies else 0.0
        )

        _print_header("RUNTIME HEALTH")
        print(f"CPU %                 : {cpu_percent:.1f}%")
        print(f"Memory Usage          : {memory_mb:.1f} MB")
        print(f"Active Sessions       : {len(self.active_sessions)}")
        print(f"Messages Processed    : {self.request_count}")
        print(f"Avg Response Time     : {avg_latency:.1f} ms")
        print(f"Uptime                : {self.uptime:.0f} sec")
        _print_divider()

    # ----------------------------
    # 11. Conversation Statistics
    # ----------------------------
    def update_conversation_stats(self, total_messages: int, avg_reply_length: float, avg_latency: float, avg_memory: float):
        self.conversation_stats["total_messages"] = total_messages
        self.conversation_stats["avg_reply_length"] = avg_reply_length
        self.conversation_stats["avg_latency"] = avg_latency
        self.conversation_stats["avg_memory_recall"] = avg_memory

    def print_conversation_stats(self):
        stats = self.conversation_stats
        _print_header("CONVERSATION STATISTICS")
        print(f"Total Messages            : {stats['total_messages']}")
        print(f"Current Session Turns     : {stats['current_session_turns']}")
        print(f"Average Reply Length      : {stats['avg_reply_length']:.1f} chars")
        print(f"Average Latency           : {stats['avg_latency']:.1f} ms")
        print(f"Average Memory Recall     : {stats['avg_memory_recall']:.1f} ms")
        _print_divider()

    # ----------------------------
    # 12. Final Terminal Format helper
    # ----------------------------
    def print_request_summary(self, metrics: RequestMetrics):
        _print_header("REQUEST SUMMARY")
        print(f"Time                   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Session                : {metrics.session_id}")
        print(f"Provider               : {metrics.provider}")
        print(f"Model                  : {metrics.model}")
        print(f"Memory                 : {metrics.memories_retrieved} retrieved, {metrics.memory_ranking:.4f} score")
        print(f"Latency                : {metrics.overall_ms:.1f} ms total")
        print(f"TTS                    : {'YES' if metrics.audio_generated else 'NO'}")
        print(f"Status                 : {'OK' if not metrics.error else 'ERROR'}")
        _print_divider()


logger = ZestyRuntimeLogger()
zesty_logger = logger
