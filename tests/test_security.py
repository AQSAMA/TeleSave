import asyncio

import pytest

from telesave.core.errors import InvalidUrlError, UnsafeUrlError
from telesave.core.security import assert_public_url, normalize_and_validate_url


def test_normalize_accepts_http_url() -> None:
    assert normalize_and_validate_url("https://example.com/file.mp4") == "https://example.com/file.mp4"


@pytest.mark.parametrize("url", ["ftp://example.com/file", "javascript:alert(1)", "not a url"])
def test_normalize_rejects_invalid_schemes(url: str) -> None:
    with pytest.raises(InvalidUrlError):
        normalize_and_validate_url(url)


def test_normalize_rejects_credentials() -> None:
    with pytest.raises(UnsafeUrlError):
        normalize_and_validate_url("https://user:pass@example.com/file")


def test_assert_public_url_rejects_loopback_ip() -> None:
    with pytest.raises(UnsafeUrlError):
        asyncio.run(assert_public_url("http://127.0.0.1/private"))
