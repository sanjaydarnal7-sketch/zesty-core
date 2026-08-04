#!/usr/bin/env python3
"""Run Sarvam TTS test sentences and verify provider logs."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("TTS_PROVIDER", "sarvam")

from tts.router import TTSRouter

TESTS = [
    ("en", "Hey Chief, I'm ready. What do you need?"),
    ("en", "All systems are online and running smoothly."),
    ("hi", "बॉस, मीटिंग पाँच बजे है, ठीक है?"),
    ("en", "Boss, meeting 5 baje hai — sab set hai na?"),
]


def main() -> None:
    router = TTSRouter()
    if not router._sarvam.is_available():
        print(f"FAIL: Sarvam not available — {router._sarvam.last_error}")
        sys.exit(1)

    passed = 0
    for label, text in TESTS:
        router.speak_text(text, label)
        if router.active_provider == "sarvam":
            print(f"PASS [{label}] provider=sarvam")
            passed += 1
        else:
            print(f"FAIL [{label}] provider={router.active_provider} err={router.last_error}")

    print(f"\n{passed}/{len(TESTS)} passed")
    sys.exit(0 if passed == len(TESTS) else 1)


if __name__ == "__main__":
    main()
