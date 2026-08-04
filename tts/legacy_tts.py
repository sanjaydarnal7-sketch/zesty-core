"""Legacy cloud TTS — ElevenLabs primary, Microsoft Edge fallback."""

from __future__ import annotations

import asyncio
import os
import subprocess
import traceback

from edge_tts import Communicate

from tts.base import TTSProvider
from tts.chunking import truncate_for_tts
from tts.normalize import normalize_for_tts
from tts.playback import play_file

try:
    from elevenlabs import ElevenLabs
except ImportError:
    ElevenLabs = None

_ELEVENLABS_VOICE_ID = "RwXLkVKnRloV1UPh3Ccx"
_ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
_OUTPUT_MP3 = "zesty_reply.mp3"


class LegacyTTSProvider(TTSProvider):
    """ElevenLabs → Edge TTS chain (previous default)."""

    name = "legacy"

    def __init__(self) -> None:
        self._elevenlabs_available = ElevenLabs is not None and bool(_ELEVENLABS_API_KEY)
        self._elevenlabs_client = None
        if self._elevenlabs_available:
            try:
                self._elevenlabs_client = ElevenLabs(api_key=_ELEVENLABS_API_KEY)
            except Exception:
                self._elevenlabs_available = False

    def is_available(self) -> bool:
        return True

    def speak(self, text: str, lang: str = "en") -> bool:
        if not text or not text.strip():
            return False
        if self._elevenlabs_available and self._speak_elevenlabs(text):
            return True
        return self._speak_edge(text, lang)

    def _speak_elevenlabs(self, text: str) -> bool:
        if not self._elevenlabs_client:
            return False
        try:
            print("[TTS] Provider: ElevenLabs")
            audio = self._elevenlabs_client.text_to_speech.convert(
                text=text,
                voice_id=_ELEVENLABS_VOICE_ID,
                model_id="eleven_turbo_v2",
            )
            audio_data = audio if isinstance(audio, bytes) else bytes(audio)
            with open(_OUTPUT_MP3, "wb") as f:
                f.write(audio_data)
            play_file(_OUTPUT_MP3, wait=True)
            return True
        except Exception as exc:
            print(f"[TTS] ElevenLabs failed: {type(exc).__name__}")
            return False

    def _speak_edge(self, text: str, lang: str) -> bool:
        normalized = truncate_for_tts(normalize_for_tts(text))
        if not normalized:
            return False

        voice = "hi-IN-SwaraNeural" if lang in ("hi", "hindi", "hinglish") else "en-US-AvaMultilingualNeural"

        async def _run() -> None:
            communicate = Communicate(normalized, voice)
            await communicate.save(_OUTPUT_MP3)

        try:
            print("[TTS] Provider: Edge TTS", flush=True)
            asyncio.run(_run())
            play_file(_OUTPUT_MP3, wait=True)
            print("[TTS] Edge TTS playback finished", flush=True)
            return True
        except Exception as exc:
            print(f"[TTS] Edge TTS failed: {exc}", flush=True)
            traceback.print_exc()
            return False
