#!/usr/bin/env bash

# Bouzouki Lesson Player installation script
# - Creates/uses a local .venv
# - Installs Python dependencies from requirements.txt
# - Checks for system tools (ffprobe, VLC) and prints guidance

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON:-python3}"

echo "[install] Using Python: $PYTHON_BIN"

# Create virtual environment if it doesn't exist
if [ ! -d .venv ]; then
  echo "[install] Creating virtual environment in .venv..."
  "$PYTHON_BIN" -m venv .venv
else
  echo "[install] Reusing existing .venv virtual environment."
fi

# Activate virtual environment
# shellcheck source=/dev/null
source .venv/bin/activate

echo "[install] Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
if [ -f requirements.txt ]; then
  echo "[install] Installing Python dependencies from requirements.txt..."
  pip install -r requirements.txt
else
  echo "[install] WARNING: requirements.txt not found; skipping Python dependency installation."
fi

# Check for ffprobe (FFmpeg)
if command -v ffprobe >/dev/null 2>&1; then
  echo "[install] ffprobe found: $(command -v ffprobe)"
else
  echo "[install] WARNING: ffprobe not found in PATH."
  echo "          Media duration/bitrate extraction may not work until FFmpeg is installed."
fi

# Check for VLC
if command -v vlc >/dev/null 2>&1; then
  echo "[install] VLC found: $(command -v vlc)"
else
  echo "[install] WARNING: VLC not found in PATH."
  echo "          Pitch-preserving audio backend (VLC) will fall back to Qt-only until VLC is installed."
fi

# Quick python-vlc import check
if python -c "import vlc" >/dev/null 2>&1; then
  echo "[install] python-vlc import OK inside .venv."
else
  echo "[install] WARNING: python-vlc could not be imported inside .venv."
  echo "          Ensure 'python-vlc' is installed and matches your system VLC."
fi

echo "[install] Installation complete. To run the app:"
echo "  source .venv/bin/activate" >&2
echo "  python main.py" >&2

