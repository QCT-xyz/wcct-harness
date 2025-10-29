#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
. .venv/bin/activate
export API_BASE=${API_BASE:-http://127.0.0.1:8000}
exec python services/ui_app/app.py
