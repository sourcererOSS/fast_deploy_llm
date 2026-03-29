#!/usr/bin/env bash
# venv + deps, systemd (uvicorn 127.0.0.1:8000), nginx HTTP site from first server{} block.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
VENV="$REPO_ROOT/.venv"
NGINX_SRC="$REPO_ROOT/deploy/nginx/llm-deploy.conf"
SYSTEMD_SRC="$REPO_ROOT/deploy/llm-deploy.service"
DEPLOY_USER="${SUDO_USER:-${USER:-$(id -un)}}"

echo "==> Python venv at $VENV"
if [[ ! -x "$VENV/bin/python" ]]; then
  "$PY" -m venv "$VENV"
fi
# shellcheck source=/dev/null
source "$VENV/bin/activate"
pip install -U pip wheel
pip install -r "$REPO_ROOT/requirements.txt"

mkdir -p "$REPO_ROOT/config" "$REPO_ROOT/logs"

echo "==> systemd: llm-deploy.service (user=$DEPLOY_USER)"
TMP_UNIT="$(mktemp)"
sed -e "s|__REPO_ROOT__|${REPO_ROOT}|g" -e "s|__DEPLOY_USER__|${DEPLOY_USER}|g" \
  "$SYSTEMD_SRC" >"$TMP_UNIT"
sudo install -m 0644 "$TMP_UNIT" /etc/systemd/system/llm-deploy.service
rm -f "$TMP_UNIT"
sudo systemctl daemon-reload
sudo systemctl enable llm-deploy.service
sudo systemctl restart llm-deploy.service
sudo systemctl --no-pager status llm-deploy.service || true

echo "==> nginx site (HTTP only — TLS via deploy/certbot-init.sh)"
tmp_ngx="$(mktemp)"
tmp_full="${tmp_ngx}.full"
sed 's/__CERTBOT_DOMAIN__/_/g' "$NGINX_SRC" >"$tmp_full"
awk '/^server \{/ { if (++n == 2) exit } { print }' "$tmp_full" >"$tmp_ngx"
rm -f "$tmp_full"
sudo install -m 0644 "$tmp_ngx" /etc/nginx/sites-available/llm-deploy
rm -f "$tmp_ngx"
sudo ln -sf /etc/nginx/sites-available/llm-deploy /etc/nginx/sites-enabled/llm-deploy
if [[ -e /etc/nginx/sites-enabled/default ]]; then
  echo "WARN: /etc/nginx/sites-enabled/default still exists — disable it if another server {} claims port 80."
fi
sudo nginx -t
sudo systemctl reload nginx

echo ""
echo "Public API base: http://<this-host>/api/v1/"
echo "Direct uvicorn:  http://127.0.0.1:8000/api/v1/"
echo "Secrets: $REPO_ROOT/config/.env (ADMIN_API_KEY, BEDROCK_ENDPOINT_API_KEY, AWS_*)."
echo "Check:           ./scripts/test.sh"
