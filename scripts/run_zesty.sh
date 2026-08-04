#!/usr/bin/env bash
# Run Zesty OS with project venv + Sarvam Bulbul v3 TTS.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "[run_zesty] Creating .venv..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "[run_zesty] Python: $(which python)"
pip install -q -r requirements-tts.txt

export TTS_PROVIDER="${TTS_PROVIDER:-sarvam}"
export SARVAM_TTS_MODEL="${SARVAM_TTS_MODEL:-bulbul:v3}"
export SARVAM_TTS_STREAM="${SARVAM_TTS_STREAM:-1}"

if [[ -z "${SARVAM_API_KEY:-}" && -z "${SARVAM_API_SUBSCRIPTION_KEY:-}" ]]; then
  echo "[run_zesty] WARNING: SARVAM_API_KEY not set — TTS will fall back to Edge"
fi

echo "[run_zesty] TTS_PROVIDER=$TTS_PROVIDER SARVAM_TTS_MODEL=$SARVAM_TTS_MODEL"

exec python main.py "$@"
