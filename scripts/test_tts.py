#!/usr/bin/env python3
"""Quick test for Zesty TTS (Sarvam Bulbul v3)."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tts.router import TTSRouter


def main() -> None:
    parser = argparse.ArgumentParser(description="Test Zesty TTS providers")
    parser.add_argument(
        "--text",
        default="Hey Chief, Zesty is online. Aaj ka vibe kya hai?",
        help="Text to synthesize",
    )
    parser.add_argument("--lang", default="en", choices=["en", "hi"], help="Language hint")
    parser.add_argument(
        "--provider",
        default="sarvam",
        choices=["sarvam", "legacy", "auto"],
        help="TTS provider mode",
    )
    args = parser.parse_args()

    import os

    os.environ["TTS_PROVIDER"] = args.provider

    router = TTSRouter()
    print(f"Speaking ({args.provider}): {args.text}")
    t1 = time.perf_counter()
    router.speak_text(args.text, args.lang)
    print(f"Done in {time.perf_counter() - t1:.2f}s | provider={router.active_provider}")


if __name__ == "__main__":
    main()
