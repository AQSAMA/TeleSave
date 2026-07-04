from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class MediaKind(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    VOICE = "voice"
    DOCUMENT = "document"


@dataclass(slots=True, frozen=True)
class DownloadRequest:
    url: str
    user_id: int
    chat_id: int


@dataclass(slots=True)
class MediaFile:
    path: Path
    kind: MediaKind = MediaKind.DOCUMENT
    filename: str | None = None
    mime_type: str | None = None
    caption: str | None = None
    title: str | None = None
    size: int | None = None


@dataclass(slots=True)
class DownloadResult:
    source_url: str
    files: list[MediaFile] = field(default_factory=list)
    title: str | None = None
    webpage_url: str | None = None
