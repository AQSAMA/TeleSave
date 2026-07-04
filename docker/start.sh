#!/usr/bin/env sh
set -eu

if [ "${TELEGRAM_LOCAL_MODE:-false}" = "true" ]; then
  if command -v telegram-bot-api >/dev/null 2>&1; then
    : "${TELEGRAM_API_ID:?TELEGRAM_API_ID is required when TELEGRAM_LOCAL_MODE=true}"
    : "${TELEGRAM_API_HASH:?TELEGRAM_API_HASH is required when TELEGRAM_LOCAL_MODE=true}"
    telegram-bot-api \
      --api-id "${TELEGRAM_API_ID}" \
      --api-hash "${TELEGRAM_API_HASH}" \
      --local \
      --http-port "${LOCAL_BOT_API_PORT:-8081}" \
      --dir "${TELEGRAM_LOCAL_DATA_DIR:-/tmp/telegram-bot-api}" &
  else
    echo "TELEGRAM_LOCAL_MODE=true but telegram-bot-api binary is not installed." >&2
    echo "Use docker-compose local-bot-api service or install the binary in this image." >&2
    exit 1
  fi
fi

exec python -m telesave.main
