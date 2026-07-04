from typing import Protocol

from telesave.core.models import DownloadResult


class Downloader(Protocol):
    async def download(self, url: str) -> DownloadResult: ...
