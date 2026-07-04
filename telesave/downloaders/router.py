from pathlib import Path
from urllib.parse import urlparse

from telesave.config import Settings
from telesave.core.models import DownloadResult
from telesave.core.security import assert_public_url
from telesave.downloaders.direct import DirectDownloader
from telesave.downloaders.ytdlp import YtDlpDownloader

_DIRECT_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".mov", ".mkv", ".webm",
    ".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".pdf", ".zip", ".rar", ".7z",
}


class DownloaderRouter:
    def __init__(self, settings: Settings, workdir: Path) -> None:
        self._direct = DirectDownloader(settings, workdir)
        self._ytdlp = YtDlpDownloader(settings, workdir)

    async def download(self, url: str) -> DownloadResult:
        await assert_public_url(url)
        suffix = Path(urlparse(url).path).suffix.lower()
        if suffix in _DIRECT_EXTENSIONS:
            return await self._direct.download(url)
        return await self._ytdlp.download(url)
