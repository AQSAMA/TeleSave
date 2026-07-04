import asyncio
import logging
import sys
from pathlib import Path

from telesave.config import Settings
from telesave.core.errors import (
    DownloadFailedError,
    DownloadTimeoutError,
    DownloadTooLargeError,
    UnsupportedSourceError,
)
from telesave.core.models import DownloadResult, MediaFile
from telesave.core.security import assert_public_url, normalize_and_validate_url
from telesave.downloaders.metadata import guess_media_kind, guess_mime_type

logger = logging.getLogger(__name__)


class YtDlpDownloader:
    def __init__(self, settings: Settings, workdir: Path) -> None:
        self._settings = settings
        self._workdir = workdir

    async def download(self, url: str) -> DownloadResult:
        normalized_url = normalize_and_validate_url(url)
        await assert_public_url(normalized_url)
        try:
            return await self._download_subprocess(normalized_url)
        except DownloadTooLargeError:
            raise
        except DownloadTimeoutError:
            raise
        except UnsupportedSourceError:
            raise
        except OSError as exc:
            raise DownloadFailedError() from exc

    async def _download_subprocess(self, url: str) -> DownloadResult:
        before = set(self._workdir.iterdir())
        process = await asyncio.create_subprocess_exec(
            *self._build_command(url),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self._settings.max_download_seconds
            )
        except TimeoutError as exc:
            process.kill()
            await process.communicate()
            raise DownloadTimeoutError() from exc
        except BaseException:
            if process.returncode is None:
                process.kill()
                await process.communicate()
            raise

        if process.returncode != 0:
            output = (stderr or b"").decode(errors="replace")
            logger.info("ytdlp_download_failed", extra={"returncode": process.returncode})
            if "Unsupported URL" in output:
                raise UnsupportedSourceError()
            if "File is larger than max-filesize" in output:
                raise DownloadTooLargeError()
            raise DownloadFailedError()

        after = [path for path in self._workdir.iterdir() if path not in before and path.is_file()]
        files: list[MediaFile] = []
        for path in after:
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
                    size=size,
                )
            )
        if not files:
            raise DownloadFailedError()
        return DownloadResult(source_url=url, files=files, webpage_url=url)

    def _build_command(self, url: str) -> list[str]:
        output_template = str(self._workdir / "%(title).180B [%(id)s].%(ext)s")
        command = [
            sys.executable,
            "-m",
            "yt_dlp",
            "--quiet",
            "--no-warnings",
            "--no-progress",
            "--output",
            output_template,
            "--format",
            self._settings.ytdlp_format
            or (
                f"best[filesize<={self._settings.max_file_size_bytes}]/"
                f"best[filesize_approx<={self._settings.max_file_size_bytes}]/best"
            ),
            "--merge-output-format",
            "mp4",
            "--retries",
            "3",
            "--fragment-retries",
            "3",
            "--socket-timeout",
            "30",
            "--continue",
            "--no-overwrites",
            "--windows-filenames",
            "--max-filesize",
            str(self._settings.max_file_size_bytes),
        ]
        if self._settings.ytdlp_cookies_file:
            command.extend(["--cookies", str(self._settings.ytdlp_cookies_file)])
        if self._settings.ytdlp_user_agent:
            command.extend(["--user-agent", self._settings.ytdlp_user_agent])
        if self._settings.ytdlp_proxy:
            command.extend(["--proxy", str(self._settings.ytdlp_proxy)])
        command.append(url)
        return command
