#!/usr/bin/env bash
# Smoke-test models + short non-stream chat via nginx (port 80) and/or direct uvicorn (8000).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
U="${SUDO_USER:-${USER:-$(id -un)}}"
HOME_DEPLOY="$(getent passwd "$U" | cut -d: -f6)"
HOME_DEPLOY="${HOME_DEPLOY:-$HOME}"
VENV="${VENV:-$HOME_DEPLOY/.venv}"
# shellcheck source=/dev/null
[[ -f "$VENV/bin/activate" ]] && source "$VENV/bin/activate"

NGINX_BASE="${NGINX_BASE:-http://127.0.0.1}"
BACKEND_BASE="${BACKEND_BASE:-http://127.0.0.1:8000}"

hdr=()
if [[ -n "${BEDROCK_ENDPOINT_API_KEY:-}" ]]; then
  hdr=(-H "Authorization: Bearer ${BEDROCK_ENDPOINT_API_KEY}")
elif [[ -f "$REPO_ROOT/config/.env" ]]; then
  key="$(grep -E '^[[:space:]]*BEDROCK_ENDPOINT_API_KEY=' "$REPO_ROOT/config/.env" | tail -1 | cut -d= -f2- | tr -d '\r')"
  if [[ -n "${key:-}" ]]; then
    hdr=(-H "Authorization: Bearer ${key}")
  fi
fi

run_curl() {
  local name="$1" url="$2"
  echo "--- $name ---"
  curl -fsS "${hdr[@]}" "$url" | head -c 800
  echo ""
  echo ""
}

echo "==> GET /api/v1/models (via nginx :80)"
run_curl "nginx" "${NGINX_BASE}/api/v1/models"

echo "==> GET /api/v1/models (direct :8000)"
run_curl "uvicorn" "${BACKEND_BASE}/api/v1/models"

echo "==> POST /api/v1/chat/completions (non-stream, nova-micro)"
BODY='{"model":"nova-micro","messages":[{"role":"user","content":"Say OK in one word."}]}'
curl -fsS "${hdr[@]}" \
  -H "Content-Type: application/json" \
  -X POST "$NGINX_BASE/api/v1/chat/completions" \
  -d "$BODY" | head -c 1200
echo ""
echo ""

echo "==> nginx static health (no app)"
curl -sS --fail "$NGINX_BASE/nginx-health"
echo ""

echo "Done."
