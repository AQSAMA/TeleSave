---
sdk: docker
app_port: 7860
---

# TeleSave

TeleSave is an asynchronous Telegram download bot designed for Docker deployments on Hugging Face Spaces. It accepts public social-media URLs and direct HTTP/HTTPS file links, downloads the content, and sends it back through Telegram.

## Features

- Async Telegram bot built with aiogram 3.
- Broad social/media support through yt-dlp.
- Direct HTTP/HTTPS streaming downloader for files.
- Optional local Telegram Bot API server mode for uploads up to 2 GB.
- Automatic Telegram send method selection for photos, videos, audio, voice, albums, and documents.
- SSRF protection for direct download URLs.
- Configurable file-size, timeout, and concurrency limits.
- Health endpoint for Hugging Face Spaces at `/healthz`.
- Safe temporary work directories with cleanup after every job.

## Deployment modes

### Option A: hosted Telegram Bot API fallback

This is the simplest mode, but it does not provide reliable 2 GB uploads.

```env
TELEGRAM_API_BASE_URL=https://api.telegram.org
TELEGRAM_LOCAL_MODE=false
```

### Option B: local Telegram Bot API server

This is the recommended mode for uploads up to 2 GB. It requires a Telegram `api_id` and `api_hash` from <https://my.telegram.org>.

```env
TELEGRAM_API_BASE_URL=http://127.0.0.1:8081
TELEGRAM_LOCAL_MODE=true
TELEGRAM_API_ID=your-api-id
TELEGRAM_API_HASH=your-api-hash
```

The Docker image builds and includes a local `telegram-bot-api` binary, and `docker/start.sh` starts it automatically when `TELEGRAM_LOCAL_MODE=true`. The Docker deployment defaults to this local mode so Hugging Face Spaces can upload files up to Telegram's 2 GB bot limit after you add `BOT_TOKEN`, `TELEGRAM_API_ID`, and `TELEGRAM_API_HASH` as Space secrets. For local development, `docker-compose.yml` runs the bot and a separate local Bot API service.

For a public Hugging Face Space, never commit a real `.env` file. Add these values in **Settings → Variables and secrets → Secrets**:

```env
BOT_TOKEN=your-bot-token-from-BotFather
TELEGRAM_API_ID=your-api-id
TELEGRAM_API_HASH=your-api-hash
```

The Docker image already sets these non-secret defaults:

```env
TELEGRAM_API_BASE_URL=http://127.0.0.1:8081
TELEGRAM_LOCAL_MODE=true
```

## Local development

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Fill in `BOT_TOKEN`.

3. Run with the hosted Bot API fallback:

```bash
pip install -e '.[dev]'
python -m telesave.main
```

4. Or run the local Bot API stack:

```bash
docker compose up --build
```

## Environment variables

See `.env.example` for the complete list.

Important settings:

- `BOT_TOKEN`: Telegram bot token from BotFather.
- `TELEGRAM_API_BASE_URL`: Hosted or local Bot API base URL.
- `TELEGRAM_LOCAL_MODE`: Enables aiogram local-file optimizations.
- `MAX_FILE_SIZE_MB`: Application-level upload limit, max 2000.
- `MAX_CONCURRENT_DOWNLOADS`: Global concurrency limit.
- `MAX_CONCURRENT_DOWNLOADS_PER_USER`: Per-user concurrency limit.
- `YTDLP_COOKIES_FILE`: Optional cookies file for sites requiring authenticated public access.

## Notes

Some platforms block automated downloads, require login cookies, or change frequently. TeleSave keeps provider support extensible by isolating download strategies behind a downloader router.
