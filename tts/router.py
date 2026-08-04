"""
TTS router — Sarvam Bulbul v3 primary, legacy cloud fallback.

Environment:
  TTS_PROVIDER=sarvam|sarvam-only|legacy|auto   (default: sarvam)
  TTS_DISABLE_FALLBACK=1                         (alias for sarvam-only behaviour)
  SARVAM_API_KEY                                 (required for Sarvam)
  SARVAM_TTS_MODEL                               (default: bulbul:v3)
  SARVAM_TTS_SPEAKER / SARVAM_TTS_SPEAKER_EN / SARVAM_TTS_SPEAKER_HI
  SARVAM_TTS_STREAM                              (default: 1 — HTTP stream API)
  SARVAM_TTS_PACE                                (default: 1.0)
  TTS_MAX_CHARS / TTS_MAX_SENTENCES              (cap long LLM replies)
"""

from __future__ import annotations

import os
import sys
import time
import traceback

os.environ.setdefault("TTS_PROVIDER", "sarvam")

from tts.base import TTSProvider
from tts.legacy_tts import LegacyTTSProvider
from tts.sarvam_tts import SarvamTTSProvider


class TTSRouter:
    """Route speech to the best available provider with automatic fallback."""

    def __init__(self) -> None:
        self._provider_mode = os.environ.get("TTS_PROVIDER", "sarvam").lower()
        self._sarvam = SarvamTTSProvider()
        self._legacy = LegacyTTSProvider()
        self._active_name = "none"
        self._last_error = ""
        self._elevenlabs_available = self._legacy._elevenlabs_available

        self._log_startup_diagnostics()

    def _fallback_disabled(self) -> bool:
        if os.environ.get("TTS_DISABLE_FALLBACK", "0").lower() in ("1", "true", "yes"):
            return True
        return self._provider_mode in ("sarvam-only", "sarvam_only")

    def _providers(self) -> list[TTSProvider]:
        if self._provider_mode == "legacy":
            return [self._legacy]
        if self._fallback_disabled() or self._provider_mode == "sarvam-only":
            return [self._sarvam]
        if self._provider_mode == "sarvam":
            return [self._sarvam, self._legacy]
        if self._sarvam.is_available():
            return [self._sarvam, self._legacy]
        return [self._legacy]

    def _log_startup_diagnostics(self) -> None:
        sarvam_ok = self._sarvam.is_available()
        print(f"[TTS] Python: {sys.executable}", flush=True)
        print(f"[TTS] Provider mode: {self._provider_mode}", flush=True)
        print(f"[TTS] Sarvam available: {sarvam_ok}", flush=True)
        if not sarvam_ok:
            err = self._sarvam.last_error or "sarvamai not configured"
            print(f"[TTS] Sarvam unavailable reason: {err}", flush=True)
        if self._provider_mode == "sarvam":
            print("[TTS] Primary: Sarvam Bulbul v3 (Edge fallback if Sarvam fails)", flush=True)

    def speak_text(self, text: str, lang: str = "en") -> None:
        preview = (text or "").strip()
        if not preview:
            print("[TTS] speak_text skipped — empty text", flush=True)
            return

        print(
            f"[TTS] speak_text called ({len(preview)} chars, lang={lang}, mode={self._provider_mode})",
            flush=True,
        )

        providers = self._providers()
        errors: list[str] = []

        for provider in providers:
            if not provider.is_available():
                reason = getattr(provider, "last_error", "") or f"{provider.name} not available"
                errors.append(reason)
                print(f"[TTS] Skipping {provider.name}: {reason}", flush=True)
                continue
            try:
                print(f"[TTS] Trying provider: {provider.name}", flush=True)
                t0 = time.perf_counter()
                if provider.speak(text, lang):
                    elapsed_ms = (time.perf_counter() - t0) * 1000
                    self._active_name = getattr(provider, "provider_label", provider.name)
                    self._last_error = ""
                    print(
                        f"[TTS] Success | provider={self._active_name} | "
                        f"provider_time={elapsed_ms:.0f}ms",
                        flush=True,
                    )
                    return
                msg = f"{provider.name} returned failure"
                errors.append(msg)
                print(f"[TTS] {msg}", flush=True)
            except Exception as exc:
                msg = f"{provider.name}: {type(exc).__name__}: {exc}"
                errors.append(msg)
                print(f"[TTS] EXCEPTION in {provider.name}: {exc}", flush=True)
                traceback.print_exc()

        self._last_error = "; ".join(errors) or "unknown"
        self._active_name = "none"
        print(f"[TTS] All providers failed — {self._last_error}", flush=True)

    @property
    def active_provider(self) -> str:
        return self._active_name

    @property
    def last_error(self) -> str:
        return self._last_error


tts_router = TTSRouter()
