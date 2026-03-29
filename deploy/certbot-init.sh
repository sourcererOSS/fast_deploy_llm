#!/usr/bin/env bash
# Let's Encrypt via certbot's nginx plugin. Only arguments — no env / .env for this script.
#
#   sudo ./deploy/certbot-init.sh <domain> <email>
#   sudo ./deploy/certbot-init.sh --staging <domain> <email>
#
# Syncs nginx from deploy/nginx/llm-deploy.conf: HTTP-only until certs exist, then HTTP+HTTPS.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NGINX_SRC="$REPO_ROOT/deploy/nginx/llm-deploy.conf"
NGINX_SITE="/etc/nginx/sites-available/llm-deploy"

usage() {
  cat <<'EOF'
Usage:
  sudo ./deploy/certbot-init.sh [--staging] <domain> <email>

Examples:
  sudo ./deploy/certbot-init.sh models.example.com admin@example.com
  sudo ./deploy/certbot-init.sh --staging models.example.com admin@example.com
EOF
}

STAGING=0
args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --staging) STAGING=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) args+=("$1"); shift ;;
  esac
done

DOMAIN="${args[0]:-}"
EMAIL="${args[1]:-}"

if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
  usage >&2
  exit 1
fi

if [[ "${EUID:-0}" -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

install_certbot() {
  if command -v certbot >/dev/null 2>&1; then
    return 0
  fi
  if command -v apt-get >/dev/null 2>&1; then
    DEBIAN_FRONTEND=noninteractive apt-get update -y
    DEBIAN_FRONTEND=noninteractive apt-get install -y certbot python3-certbot-nginx
  elif command -v dnf >/dev/null 2>&1; then
    dnf install -y certbot python3-certbot-nginx || dnf install -y certbot
  elif command -v yum >/dev/null 2>&1; then
    yum install -y certbot python3-certbot-nginx || yum install -y certbot
  else
    echo "Install certbot + python3-certbot-nginx manually, then re-run." >&2
    exit 1
  fi
}

install_certbot

ensure_nginx() {
  if ! command -v nginx >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then
      DEBIAN_FRONTEND=noninteractive apt-get install -y nginx
    elif command -v dnf >/dev/null 2>&1; then
      dnf install -y nginx
    elif command -v yum >/dev/null 2>&1; then
      yum install -y nginx
    else
      echo "Install nginx, then re-run." >&2
      exit 1
    fi
  fi
}

ensure_nginx

if [[ ! -f "$NGINX_SRC" ]]; then
  echo "Missing nginx template: $NGINX_SRC" >&2
  exit 1
fi

# Render template: full TLS + HTTP. Until certs exist, only the first server {} is active.
apply_nginx_from_repo() {
  local tmp_full
  tmp_full="$(mktemp)"
  sed "s/__CERTBOT_DOMAIN__/${DOMAIN}/g" "$NGINX_SRC" >"$tmp_full"

  if [[ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]]; then
    install -m 0644 "$tmp_full" "$NGINX_SITE"
  else
    awk '/^server \{/ { if (++n == 2) exit } { print }' "$tmp_full" >"$NGINX_SITE"
    chmod 0644 "$NGINX_SITE"
  fi
  rm -f "$tmp_full"
}

if [[ ! -f "$NGINX_SITE" ]] || [[ ! -e /etc/nginx/sites-enabled/llm-deploy ]]; then
  echo "==> Installing nginx site from repo"
  apply_nginx_from_repo
  ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/llm-deploy
  if [[ -e /etc/nginx/sites-enabled/default ]]; then
    echo "WARN: /etc/nginx/sites-enabled/default still enabled — disable if port 80 conflicts." >&2
  fi
else
  apply_nginx_from_repo
fi

if command -v systemctl >/dev/null 2>&1; then
  systemctl enable nginx 2>/dev/null || true
  systemctl start nginx 2>/dev/null || true
fi

nginx -t
systemctl reload nginx

extra=()
[[ "$STAGING" -eq 1 ]] && extra+=(--staging)

echo "==> Certificate for $DOMAIN (nginx plugin)"
if certbot --nginx \
  --non-interactive \
  --agree-tos \
  --email "$EMAIL" \
  -d "$DOMAIN" \
  "${extra[@]}" \
  --redirect
then
  echo "==> Sync full site config (HTTP + TLS) from repo"
  sed "s/__CERTBOT_DOMAIN__/${DOMAIN}/g" "$NGINX_SRC" >"$NGINX_SITE"
  nginx -t
  systemctl reload nginx
else
  echo "certbot failed — nginx left on HTTP-only until this succeeds." >&2
  exit 1
fi

# echo "Done: https://${DOMAIN}/api/v1/"
# echo "Dry-run: certbot renew --dry-run"
