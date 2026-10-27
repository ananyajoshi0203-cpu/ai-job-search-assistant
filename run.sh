#!/usr/bin/env bash
# One-line start (macOS/Linux): ./run.sh — sets up and opens the app.
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
command -v jobhunt >/dev/null 2>&1 || python -m pip install -e .
jobhunt app
