#!/usr/bin/env sh
set -eu

if [ "${TELEGRAM_LOCAL_MODE:-false}" = "true" ]; then
  api_base_url="${TELEGRAM_API_BASE_URL:-https://api.telegram.org}"
  readiness_target="$(
    python - "${api_base_url}" <<'PY'
import sys
from urllib.parse import urlparse

url = urlparse(sys.argv[1])
if not url.hostname:
    raise SystemExit(f"TELEGRAM_API_BASE_URL must include a hostname: {sys.argv[1]}")
port = url.port
if port is None:
    port = 443 if url.scheme == "https" else 80
print(f"{url.hostname}:{port}")
PY
  )"
  api_host="${readiness_target%:*}"
  api_port="${readiness_target##*:}"

  should_start_local_api=false
  case "${api_host}" in
    127.0.0.1|localhost)
      should_start_local_api=true
      ;;
  esac

  if [ "${should_start_local_api}" = "true" ] && command -v telegram-bot-api >/dev/null 2>&1; then
    local_api_port="${LOCAL_BOT_API_PORT:-${api_port}}"
    : "${TELEGRAM_API_ID:?TELEGRAM_API_ID is required when TELEGRAM_LOCAL_MODE=true}"
    : "${TELEGRAM_API_HASH:?TELEGRAM_API_HASH is required when TELEGRAM_LOCAL_MODE=true}"
    telegram-bot-api \
      --api-id "${TELEGRAM_API_ID}" \
      --api-hash "${TELEGRAM_API_HASH}" \
      --local \
      --http-port "${local_api_port}" \
      --dir "${TELEGRAM_LOCAL_DATA_DIR:-/tmp/telegram-bot-api}" &
  elif [ "${should_start_local_api}" = "true" ]; then
    echo "TELEGRAM_LOCAL_MODE=true but telegram-bot-api binary is not installed." >&2
    echo "Use docker-compose local-bot-api service or install the binary in this image." >&2
    exit 1
  fi

  for _ in $(seq 1 "${TELEGRAM_API_READY_TIMEOUT_SECONDS:-30}"); do
    if python -c "import socket; socket.create_connection(('${api_host}', ${api_port}), 1).close()" >/dev/null 2>&1; then
      api_ready=true
      break
    fi
    api_ready=false
    sleep 1
  done

  if [ "${api_ready}" != "true" ]; then
    echo "Telegram Bot API endpoint ${api_base_url} did not become ready." >&2
    exit 1
  fi
fi

exec python -m telesave.main
