import logging
from email.message import Message
from pathlib import Path
from urllib.parse import unquote, urlparse

import aiofiles
import httpx

from telesave.config import Settings
from telesave.core.errors import DownloadFailedError, DownloadTooLargeError
from telesave.core.models import DownloadResult, MediaFile
from telesave.core.security import assert_public_url
from telesave.downloaders.metadata import guess_media_kind, guess_mime_type

logger = logging.getLogger(__name__)


class DirectDownloader:
    def __init__(self, settings: Settings, workdir: Path) -> None:
        self._settings = settings
        self._workdir = workdir

    async def download(self, url: str) -> DownloadResult:
        await assert_public_url(url)
        timeout = httpx.Timeout(
            connect=self._settings.direct_download_connect_timeout,
            read=self._settings.direct_download_read_timeout,
            write=30.0,
            pool=30.0,
        )
        async with httpx.AsyncClient(
            follow_redirects=True,
            max_redirects=self._settings.direct_download_max_redirects,
            timeout=timeout,
            headers={"User-Agent": self._settings.ytdlp_user_agent or "TeleSaveBot/0.1"},
        ) as client:
            async with client.stream("GET", url) as response:
                if response.status_code >= 400:
                    raise DownloadFailedError()
                await assert_public_url(str(response.url))
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self._settings.max_file_size_bytes:
                    raise DownloadTooLargeError()
                filename = self._filename_from_headers(response.headers) or self._filename_from_url(
                    str(response.url)
                )
                path = self._workdir / filename
                total = 0
                async with aiofiles.open(path, "wb") as file:
                    async for chunk in response.aiter_bytes(self._settings.direct_download_chunk_size):
                        total += len(chunk)
                        if total > self._settings.max_file_size_bytes:
                            raise DownloadTooLargeError()
                        await file.write(chunk)
        mime_type = guess_mime_type(path)
        return DownloadResult(
            source_url=url,
            files=[
                MediaFile(
                    path=path,
                    kind=guess_media_kind(path, mime_type),
                    filename=filename,
                    mime_type=mime_type,
                    size=path.stat().st_size,
                )
            ],
        )

    @staticmethod
    def _filename_from_headers(headers: httpx.Headers) -> str | None:
        value = headers.get("content-disposition")
        if not value:
            return None
        message = Message()
        message["content-disposition"] = value
        filename = message.get_filename()
        return Path(filename).name if filename else None

    @staticmethod
    def _filename_from_url(url: str) -> str:
        name = Path(unquote(urlparse(url).path)).name
        return name or "download.bin"
