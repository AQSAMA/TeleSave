import asyncio
import logging
from pathlib import Path
from typing import Any

import yt_dlp

from telesave.config import Settings
from telesave.core.errors import DownloadFailedError, DownloadTooLargeError, UnsupportedSourceError
from telesave.core.models import DownloadResult, MediaFile
from telesave.core.security import normalize_and_validate_url
from telesave.downloaders.metadata import guess_media_kind, guess_mime_type

logger = logging.getLogger(__name__)


class YtDlpDownloader:
    def __init__(self, settings: Settings, workdir: Path) -> None:
        self._settings = settings
        self._workdir = workdir

    async def download(self, url: str) -> DownloadResult:
        normalize_and_validate_url(url)
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._download_blocking, url),
                timeout=self._settings.max_download_seconds,
            )
        except TimeoutError as exc:
            raise DownloadFailedError() from exc
        except DownloadTooLargeError:
            raise
        except yt_dlp.utils.UnsupportedError as exc:
            raise UnsupportedSourceError() from exc
        except yt_dlp.utils.DownloadError as exc:
            raise DownloadFailedError() from exc

    def _download_blocking(self, url: str) -> DownloadResult:
        output_template = str(self._workdir / "%(title).180B [%(id)s].%(ext)s")
        options: dict[str, Any] = {
            "outtmpl": output_template,
            "format": self._settings.ytdlp_format
            or (
                f"best[filesize<={self._settings.max_file_size_bytes}]/"
                f"best[filesize_approx<={self._settings.max_file_size_bytes}]/best"
            ),
            "merge_output_format": "mp4",
            "noplaylist": False,
            "quiet": True,
            "no_warnings": True,
            "retries": 3,
            "fragment_retries": 3,
            "socket_timeout": 30,
            "continuedl": True,
            "overwrites": False,
            "restrictfilenames": False,
            "windowsfilenames": True,
            "max_filesize": self._settings.max_file_size_bytes,
        }
        if self._settings.ytdlp_cookies_file:
            options["cookiefile"] = str(self._settings.ytdlp_cookies_file)
        if self._settings.ytdlp_user_agent:
            options["user_agent"] = self._settings.ytdlp_user_agent
        if self._settings.ytdlp_proxy:
            options["proxy"] = str(self._settings.ytdlp_proxy)

        before = set(self._workdir.iterdir())
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
        after = [path for path in self._workdir.iterdir() if path not in before and path.is_file()]
        if not after:
            downloaded = yt_dlp.utils.traverse_obj(
                info, ("requested_downloads", ..., "filepath")
            ) or []
            after = [Path(path) for path in downloaded]
        files: list[MediaFile] = []
        title = info.get("title") if isinstance(info, dict) else None
        for path in after:
            if not path.exists() or not path.is_file():
                continue
            size = path.stat().st_size
            if size > self._settings.max_file_size_bytes:
                raise DownloadTooLargeError()
            mime_type = guess_mime_type(path)
            files.append(
                MediaFile(
                    path=path,
                    kind=guess_media_kind(path, mime_type),
                    filename=path.name,
                    mime_type=mime_type,
                    caption=title,
                    title=title,
                    size=size,
                )
            )
        if not files:
            raise DownloadFailedError()
        return DownloadResult(source_url=url, files=files, title=title, webpage_url=url)
