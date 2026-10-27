#!/usr/bin/env bash
# Run Pic2Cookie locally.
#   scripts/start.sh         build the frontend once, then serve everything on :8000
#   scripts/start.sh --dev   API with auto-reload on :8000 + Vite dev server on :5173
set -euo pipefail
cd "$(dirname "$0")/.."

need() { command -v "$1" >/dev/null || { echo "Please install $1 ($2)" >&2; exit 1; }; }
need uv "https://docs.astral.sh/uv/"
need npm "https://nodejs.org/"

uv sync
(cd frontend && npm ci --no-audit --no-fund)

if [[ "${1:-}" == "--dev" ]]; then
  uv run pic2cookie serve --reload &
  api=$!
  trap 'kill $api 2>/dev/null' EXIT
  (cd frontend && npm run dev)
else
  (cd frontend && npm run build)
  echo "Pic2Cookie runs on http://127.0.0.1:${PIC2COOKIE_PORT:-8000}"
  exec uv run pic2cookie serve
fi
