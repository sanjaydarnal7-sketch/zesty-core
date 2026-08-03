import os
import asyncio
import subprocess
import re

try:
    from elevenlabs import ElevenLabs
except ImportError:
    ElevenLabs = None
ELEVENLABS_AVAILABLE = ElevenLabs is not None

from edge_tts import Communicate

_ELEVENLABS_VOICE_ID = "RwXLkVKnRloV1UPh3Ccx"
_ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")


def _normalize_for_tts(text: str) -> str:
    if not text:
        return ""

    normalized = text.strip()
    normalized = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', normalized)
    normalized = re.sub(r'^#{1,6}\s+', '', normalized, flags=re.MULTILINE)
    normalized = re.sub(r'^[-•]\s+', '', normalized, flags=re.MULTILINE)
    normalized = re.sub(r'<[^>]+>', '', normalized)
    normalized = re.sub(r'\[TARGET_PANEL:\s*[A-Za-z_]+\]', '', normalized).strip()
    normalized = re.sub(r'\.{3,}', '...', normalized)
    normalized = re.sub(r'([.,!?])([^\s])', r'\1 \2', normalized)
    normalized = re.sub(r'\n{3,}', '\n\n', normalized)

    lines = normalized.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    normalized = " ".join(cleaned_lines)

    return normalized


class TTSRouter:
    """Production-grade TTS routing with ElevenLabs primary and Edge TTS fallback."""

    def __init__(self):
        self._elevenlabs_available = ELEVENLABS_AVAILABLE and bool(_ELEVENLABS_API_KEY)
        self._elevenlabs_client = None
        if self._elevenlabs_available:
            try:
                self._elevenlabs_client = ElevenLabs(api_key=_ELEVENLABS_API_KEY)
            except Exception:
                self._elevenlabs_available = False

    def _speak_elevenlabs(self, text: str) -> bool:
        """Attempt to speak using ElevenLabs. Returns True on success."""
        if not self._elevenlabs_client:
            return False

        try:
            print("[TTS] Provider: ElevenLabs")
            audio = self._elevenlabs_client.text_to_speech.convert(
                text=text,
                voice_id=_ELEVENLABS_VOICE_ID,
                model_id="eleven_turbo_v2"
            )
            
            audio_data = audio if isinstance(audio, bytes) else bytes(audio)
            
            with open("zesty_reply.mp3", "wb") as f:
                f.write(audio_data)
            
            subprocess.Popen(
                ["afplay", "zesty_reply.mp3"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception as e:
            print(f"[TTS] ElevenLabs failed: {type(e).__name__}")
            return False

    def _speak_edge_tts(self, text: str, lang: str = "en") -> bool:
        """Fallback to Edge TTS. Returns True on success."""
        normalized = _normalize_for_tts(text)
        if not normalized:
            return False

        voice = "en-US-AvaMultilingualNeural" if lang == "en" else "hi-IN-SwaraNeural"

        async def _tts():
            communicate = Communicate(normalized, voice)
            await communicate.save("zesty_reply.mp3")

        try:
            print("[TTS] ElevenLabs failed")
            print("[TTS] Switching to Edge TTS")
            print("[TTS] Provider: Edge")
            asyncio.run(_tts())
            subprocess.Popen(
                ["afplay", "zesty_reply.mp3"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception as e:
            print(f"[TTS] Edge TTS failed: {e}")
            return False

    def speak_text(self, text: str, lang: str = "en"):
        """Speak text using ElevenLabs first, fallback to Edge TTS."""
        if not text or not text.strip():
            return

        if self._elevenlabs_available:
            if self._speak_elevenlabs(text):
                return
        
        self._speak_edge_tts(text, lang)


tts_router = TTSRouter()