#!/usr/bin/env bash
# SlideCraft Lite launcher — creates venv, installs deps, runs server.
# Usage:  ./run.sh                  (localhost-only)
#         HOST=0.0.0.0 ./run.sh     (LAN-accessible, no auth)
set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    echo ">> First run: creating .venv"
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if ! python -c "import flask" 2>/dev/null; then
    echo ">> Installing deps (no torch, no ffmpeg — ~250 MB)"
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# LibreOffice is OPTIONAL. PDF upload + every export work without it.
# Only PPTX upload needs it (PPTX -> PDF -> JPG).
_lo_found() {
    command -v libreoffice >/dev/null 2>&1 || \
    command -v soffice >/dev/null 2>&1 || \
    [ -e "/Applications/LibreOffice.app/Contents/MacOS/soffice" ]
}
if ! _lo_found; then
    echo ""
    echo "[info] LibreOffice not found — PDF upload still works."
    echo "       For PPTX upload, install LibreOffice:"
    echo "         macOS: brew install --cask libreoffice"
    echo "         apt:   sudo apt install libreoffice"
    echo "         dnf:   sudo dnf install libreoffice"
    echo ""
fi

exec .venv/bin/python app.py
