from pathlib import Path

from telesave.core.models import MediaKind
from telesave.downloaders.metadata import guess_media_kind


def test_guess_video_kind() -> None:
    assert guess_media_kind(Path("clip.mp4"), "video/mp4") is MediaKind.VIDEO


def test_guess_photo_kind() -> None:
    assert guess_media_kind(Path("image.jpg"), "image/jpeg") is MediaKind.PHOTO


def test_guess_document_fallback() -> None:
    assert guess_media_kind(Path("archive.zip"), "application/zip") is MediaKind.DOCUMENT
