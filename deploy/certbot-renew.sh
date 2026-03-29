#!/usr/bin/env bash
# Manual renewal check (systemd timer usually runs this twice daily).
# Usage: sudo ./deploy/certbot-renew.sh

sudo sed "s/__CERTBOT_DOMAIN__/models.neurofx.co/g" \
  /home/ubuntu/libs/llm_deploy/deploy/nginx/llm-deploy.conf \
  | sudo tee /etc/nginx/sites-available/llm-deploy > /dev/null

sudo nginx -t && sudo systemctl reload nginx

set -euo pipefail

if [[ "${EUID:-0}" -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

# Deploy hooks under /etc/letsencrypt/renewal-hooks/deploy/ run after a successful renew.
certbot renew --quiet
echo "Renewal pass finished."
