import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

from .errors import InvalidUrlError, UnsafeUrlError

_UNSAFE_HOSTS = {"localhost", "metadata.google.internal"}


def normalize_and_validate_url(raw: str) -> str:
    value = raw.strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise InvalidUrlError()
    if parsed.username or parsed.password:
        raise UnsafeUrlError()
    if not parsed.hostname:
        raise InvalidUrlError()
    try:
        _ = parsed.port
    except ValueError as exc:
        raise InvalidUrlError() from exc
    return value


def _is_public_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return not any(
        [
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        ]
    )


async def assert_public_url(url: str) -> None:
    parsed = urlparse(normalize_and_validate_url(url))
    hostname = parsed.hostname
    if hostname is None or hostname.lower() in _UNSAFE_HOSTS:
        raise UnsafeUrlError()
    try:
        ipaddress.ip_address(hostname)
        addresses = [hostname]
    except ValueError:
        loop = asyncio.get_running_loop()
        infos = await loop.getaddrinfo(hostname, parsed.port, type=socket.SOCK_STREAM)
        addresses = [info[4][0] for info in infos]
    if not addresses or any(not _is_public_ip(address) for address in addresses):
        raise UnsafeUrlError()
