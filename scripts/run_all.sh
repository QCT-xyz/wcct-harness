#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
if [ -f .venv/bin/activate ]; then . .venv/bin/activate; fi
python scripts/run_all.py
