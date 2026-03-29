#!/usr/bin/env bash
# Re-sync nginx from repo template, then certbot renew.
# Usage:
#   sudo ./deploy/certbot-renew.sh <domain>
#   sudo CERTBOT_DOMAIN=models.example.com ./deploy/certbot-renew.sh
set -euo pipefail

if [[ "${EUID:-0}" -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOMAIN="${1:-${CERTBOT_DOMAIN:-}}"
if [[ -z "$DOMAIN" ]]; then
  echo "Usage: sudo $0 <domain>  (or set CERTBOT_DOMAIN)" >&2
  exit 1
fi

NGINX_SRC="$REPO_ROOT/deploy/nginx/fast-deploy-llm.conf"
NGINX_SITE="/etc/nginx/sites-available/fast-deploy-llm"

if [[ ! -f "$NGINX_SRC" ]]; then
  echo "Missing $NGINX_SRC" >&2
  exit 1
fi

sed "s/__CERTBOT_DOMAIN__/${DOMAIN}/g" "$NGINX_SRC" | tee "$NGINX_SITE" >/dev/null
nginx -t && systemctl reload nginx

certbot renew --quiet
echo "Renewal pass finished."
