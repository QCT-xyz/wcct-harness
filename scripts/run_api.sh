#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
if [ -f .venv/bin/activate ]; then . .venv/bin/activate; fi
exec uvicorn services.poisson_api.main:app --host 127.0.0.1 --port 8000
