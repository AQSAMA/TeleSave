import asyncio
from pathlib import Path

import pytest
from pydantic import SecretStr

from telesave.config import Settings
from telesave.core.errors import UnsafeUrlError
from telesave.downloaders.router import DownloaderRouter


def _settings(tmp_path: Path) -> Settings:
    return Settings(BOT_TOKEN=SecretStr("123:test"), APP_ENV="test", TEMP_DIR=tmp_path)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://169.254.169.254/latest/meta-data/",
    ],
)
def test_router_rejects_private_urls_before_ytdlp(url: str, tmp_path: Path) -> None:
    router = DownloaderRouter(_settings(tmp_path), tmp_path)

    with pytest.raises(UnsafeUrlError):
        asyncio.run(router.download(url))
