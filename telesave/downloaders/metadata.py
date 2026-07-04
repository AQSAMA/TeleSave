import mimetypes
from pathlib import Path

from telesave.core.models import MediaKind


def guess_mime_type(path: Path) -> str | None:
    return mimetypes.guess_type(path.name)[0]


def guess_media_kind(path: Path, mime_type: str | None) -> MediaKind:
    mime = mime_type or ""
    suffix = path.suffix.lower()
    if mime.startswith("image/") and suffix not in {".gif", ".svg"}:
        return MediaKind.PHOTO
    if mime.startswith("video/"):
        return MediaKind.VIDEO
    if mime.startswith("audio/"):
        return MediaKind.VOICE if suffix in {".ogg", ".opus"} else MediaKind.AUDIO
    return MediaKind.DOCUMENT
