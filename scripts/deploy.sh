#!/usr/bin/env bash
# Install or turn off systemd fast-deploy-llm.service (uvicorn in screen — see deploy/fast-deploy-llm.service).
# Usage:
#   ./scripts/deploy.sh           # install unit, enable + restart
#   ./scripts/deploy.sh disable   # stop and disable (does not remove unit file)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CMD="${1:-install}"

case "$CMD" in
  disable|off|stop)
    sudo systemctl disable --now fast-deploy-llm.service
    echo "fast-deploy-llm.service disabled and stopped (unit file still in /etc/systemd/system/)."
    ;;
  install)
    USER_DEPLOY="${SUDO_USER:-${USER:-$(id -un)}}"
    TARGET_HOME="$(getent passwd "$USER_DEPLOY" | cut -d: -f6)"
    TARGET_HOME="${TARGET_HOME:-$HOME}"
    LLM_DEPLOY_VENV="${LLM_DEPLOY_VENV:-${VENV:-$TARGET_HOME/.venv}}"

    mkdir -p "$REPO_ROOT/config" "$REPO_ROOT/logs"

    sed -e "s|__REPO_ROOT__|${REPO_ROOT}|g" \
      -e "s|__DEPLOY_USER__|${USER_DEPLOY}|g" \
      -e "s|__VENV__|${LLM_DEPLOY_VENV}|g" \
      "$REPO_ROOT/deploy/fast-deploy-llm.service" | sudo tee /etc/systemd/system/fast-deploy-llm.service >/dev/null
    sudo systemctl daemon-reload
    sudo systemctl enable fast-deploy-llm.service
    sudo systemctl restart fast-deploy-llm.service

    echo "systemd: fast-deploy-llm.service  |  venv: $LLM_DEPLOY_VENV  |  app: http://127.0.0.1:8000/api/v1/  |  config: $REPO_ROOT/config/.env"
    echo "Deactivate: ./scripts/deploy.sh disable"
    ;;
  -h|--help|help)
    echo "Usage: $0 [install|disable]"
    echo "  install  — write unit, daemon-reload, enable + restart (default)"
    echo "  disable  — systemctl disable --now fast-deploy-llm.service"
    ;;
  *)
    echo "Unknown command: $CMD (try: install, disable, --help)" >&2
    exit 1
    ;;
esac
