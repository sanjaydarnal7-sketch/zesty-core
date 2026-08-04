"""Sarvam AI Bulbul v3 TTS — low-latency cloud API for Indian languages + Hinglish."""

from __future__ import annotations

import base64
import os
import subprocess
import sys
import time
import traceback
from typing import Any

from tts.base import TTSProvider
from tts.chunking import truncate_for_tts
from tts.lang_detect import detect_speech_language
from tts.normalize import normalize_for_tts, resolve_sarvam_config
from tts.playback import play_file

_DEFAULT_MODEL = "bulbul:v3"
_OUTPUT_AUDIO = "zesty_reply.mp3"


class SarvamTTSProvider(TTSProvider):
    """
    Sarvam Bulbul v3 — India-hosted TTS with native Hinglish code-switching.

  Requires SARVAM_API_KEY (or SARVAM_API_SUBSCRIPTION_KEY) in the environment.
    """

    name = "sarvam"

    def __init__(self) -> None:
        self._client: Any = None
        self._import_ok: bool | None = None
        self._import_error: str = ""
        self._active_provider_label = self.name

    @property
    def last_error(self) -> str:
        return self._import_error

    def is_available(self) -> bool:
        if self._import_ok is not None:
            return self._import_ok
        api_key = _api_key()
        if not api_key:
            self._import_ok = False
            self._import_error = (
                "SARVAM_API_KEY not set. Get a free key at https://www.sarvam.ai"
            )
            return False
        try:
            from sarvamai import SarvamAI  # noqa: F401

            self._import_ok = True
            self._import_error = ""
        except ImportError as exc:
            self._import_ok = False
            self._import_error = (
                f"ImportError: {exc} (python={sys.executable}). "
                "Run: pip install sarvamai"
            )
        return self._import_ok

    @property
    def provider_label(self) -> str:
        return self._active_provider_label

    def preload(self) -> bool:
        """No model to load — verify API client initializes."""
        try:
            self._ensure_client()
            return True
        except Exception as exc:
            print(f"[TTS] Sarvam preload failed: {exc}")
            return False

    def speak(self, text: str, lang: str = "english") -> bool:
        normalized = truncate_for_tts(normalize_for_tts(text))
        if not normalized:
            return False

        try:
            dialect = detect_speech_language(normalized, lang)
            language_code, speaker = resolve_sarvam_config(normalized, lang)
            model = os.environ.get("SARVAM_TTS_MODEL", _DEFAULT_MODEL)
            pace = float(os.environ.get("SARVAM_TTS_PACE", "1.08"))
            temperature = float(os.environ.get("SARVAM_TTS_TEMPERATURE", "0.78"))
            preprocess = os.environ.get("SARVAM_TTS_PREPROCESS", "1").lower() not in (
                "0",
                "false",
                "no",
            )
            use_stream = os.environ.get("SARVAM_TTS_STREAM", "1").lower() not in (
                "0",
                "false",
                "no",
            )

            print(
                f"[TTS] Provider: sarvam | speaker={speaker} | dialect={dialect} | "
                f"lang={language_code} | stream={use_stream} | chars={len(normalized)}",
                flush=True,
            )

            client = self._ensure_client()
            t0 = time.perf_counter()
            synth_kwargs = dict(
                text=normalized,
                language_code=language_code,
                speaker=speaker,
                model=model,
                pace=pace,
                temperature=temperature,
                enable_preprocessing=preprocess,
            )

            if use_stream:
                ok = self._speak_stream(client, **synth_kwargs)
            else:
                ok = self._speak_rest(client, **synth_kwargs)

            if ok:
                print(
                    f"[TTS] Sarvam done in {(time.perf_counter() - t0) * 1000:.0f}ms",
                    flush=True,
                )
                self._active_provider_label = self.name
            return ok
        except Exception as exc:
            print(f"[TTS] Sarvam failed: {type(exc).__name__}: {exc}")
            traceback.print_exc()
            return False

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        from sarvamai import SarvamAI

        self._client = SarvamAI(api_subscription_key=_api_key())
        return self._client

    def _speak_stream(self, client: Any, **kwargs: Any) -> bool:
        """HTTP stream — low first-byte latency, smooth full-file playback."""
        t_first: float | None = None
        t_gen_start = time.perf_counter()

        stream_kwargs = {**kwargs, "output_audio_codec": "mp3"}
        with open(_OUTPUT_AUDIO, "wb") as f:
            for chunk in client.text_to_speech.convert_stream(**stream_kwargs):
                if t_first is None:
                    t_first = time.perf_counter()
                f.write(chunk)

        if t_first:
            print(
                f"[TTS] Sarvam time-to-first-audio: "
                f"{(t_first - t_gen_start) * 1000:.0f}ms",
                flush=True,
            )

        return self._play_file(_OUTPUT_AUDIO)

    def _speak_rest(self, client: Any, **kwargs: Any) -> bool:
        """REST batch synthesis — simple fallback path."""
        rest_kwargs = {**kwargs, "output_audio_codec": "mp3"}
        response = client.text_to_speech.convert(**rest_kwargs)
        audio_bytes = _decode_response_audio(response)
        if not audio_bytes:
            print("[TTS] Sarvam produced empty audio", flush=True)
            return False
        with open(_OUTPUT_AUDIO, "wb") as f:
            f.write(audio_bytes)
        return self._play_file(_OUTPUT_AUDIO)

    @staticmethod
    def _play_file(path: str) -> bool:
        if not os.path.isfile(path) or os.path.getsize(path) == 0:
            print("[TTS] Sarvam audio file missing or empty", flush=True)
            return False
        print("[TTS] Sarvam playback started", flush=True)
        return play_file(path, wait=True)


def _api_key() -> str:
    return (
        os.environ.get("SARVAM_API_KEY", "")
        or os.environ.get("SARVAM_API_SUBSCRIPTION_KEY", "")
    ).strip()


def _decode_response_audio(response: Any) -> bytes:
    if response is None:
        return b""
    audios = getattr(response, "audios", None)
    if audios:
        joined = "".join(audios)
        return base64.b64decode(joined)
    if isinstance(response, bytes):
        return response
    return b""
