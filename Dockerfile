FROM aiogram/telegram-bot-api:10.1 AS telegram-bot-api

FROM python:3.12-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    TEMP_DIR=/tmp/telesave \
    TELEGRAM_API_BASE_URL=http://127.0.0.1:8081 \
    TELEGRAM_LOCAL_MODE=true

RUN apk add --no-cache \
        ffmpeg \
        ca-certificates \
        curl \
        libstdc++ \
        openssl \
        zlib

WORKDIR /app

COPY --from=telegram-bot-api /usr/local/bin/telegram-bot-api /usr/local/bin/telegram-bot-api

COPY pyproject.toml README.md ./
COPY telesave ./telesave
COPY docker/start.sh ./docker/start.sh

RUN pip install --upgrade pip \
    && pip install . \
    && adduser -D -s /sbin/nologin appuser \
    && mkdir -p /tmp/telesave /tmp/telegram-bot-api \
    && chown -R appuser:appuser /app /tmp/telesave /tmp/telegram-bot-api

USER appuser
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/healthz" || exit 1

CMD ["./docker/start.sh"]
