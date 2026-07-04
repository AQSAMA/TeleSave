FROM debian:bookworm-slim AS telegram-bot-api-builder

ARG TELEGRAM_BOT_API_REF=master

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        cmake \
        g++ \
        gperf \
        git \
        make \
        libssl-dev \
        zlib1g-dev \
    && git clone --recursive --depth 1 --branch "${TELEGRAM_BOT_API_REF}" \
        https://github.com/tdlib/telegram-bot-api.git /src/telegram-bot-api \
    && cmake -S /src/telegram-bot-api -B /src/telegram-bot-api/build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
    && cmake --build /src/telegram-bot-api/build --target install --parallel "$(nproc)"

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    TEMP_DIR=/tmp/telesave \
    TELEGRAM_API_BASE_URL=http://127.0.0.1:8081 \
    TELEGRAM_LOCAL_MODE=true

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=telegram-bot-api-builder /usr/local/bin/telegram-bot-api /usr/local/bin/telegram-bot-api

COPY pyproject.toml README.md ./
COPY telesave ./telesave
COPY docker/start.sh ./docker/start.sh

RUN pip install --upgrade pip \
    && pip install . \
    && useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /tmp/telesave /tmp/telegram-bot-api \
    && chown -R appuser:appuser /app /tmp/telesave /tmp/telegram-bot-api

USER appuser
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/healthz" || exit 1

CMD ["./docker/start.sh"]
