from __future__ import annotations

import httpx
import pytest

from app.integrations.exceptions import (
    QBittorrentAuthError,
    QBittorrentError,
    QBittorrentForbiddenError,
    QBittorrentServerError,
    QBittorrentTimeoutError,
)
from app.integrations.qbittorrent.client import QBittorrentClient
from app.schemas.qbittorrent import QBittorrentHealth


def make_mock_transport(
    responses: list[tuple[int, str]],
) -> httpx.MockTransport:
    """Return a transport that cycles through (status_code, body) pairs."""
    iterator = iter(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        status, body = next(iterator)
        return httpx.Response(status, content=body.encode())

    return httpx.MockTransport(handler)


def make_qbittorrent_client(
    status_code: int = 200,
    body: str = "Ok.",
) -> QBittorrentClient:
    http = httpx.AsyncClient(
        transport=make_mock_transport([(status_code, body)]),
        base_url="http://qbittorrent.test",
    )
    return QBittorrentClient(http, username="admin", password="password")


def make_authenticated_client(
    status_code: int = 200,
    body: str = "",
) -> QBittorrentClient:
    """Client with _authenticated=True to skip login in tests."""
    http = httpx.AsyncClient(
        transport=make_mock_transport([(status_code, body)]),
        base_url="http://qbittorrent.test",
    )
    client = QBittorrentClient(http, username="admin", password="password")
    client._authenticated = True
    return client


# ---------------------------------------------------------------------------
# login()
# ---------------------------------------------------------------------------


async def test_login_ok_sets_authenticated() -> None:
    client = make_qbittorrent_client(status_code=200, body="Ok.")

    await client.login()

    assert client._authenticated is True


async def test_login_fails_body_raises_auth_error() -> None:
    client = make_qbittorrent_client(status_code=200, body="Fails.")

    with pytest.raises(QBittorrentAuthError):
        await client.login()


async def test_login_403_raises_forbidden() -> None:
    client = make_qbittorrent_client(status_code=403, body="")

    with pytest.raises(QBittorrentForbiddenError):
        await client.login()


async def test_login_timeout_raises_timeout_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out")

    http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://qbittorrent.test",
    )
    client = QBittorrentClient(http, username="admin", password="password")

    with pytest.raises(QBittorrentTimeoutError):
        await client.login()


# ---------------------------------------------------------------------------
# health()
# ---------------------------------------------------------------------------


async def test_health_calls_login_first() -> None:
    """Fresh client: login is called before the version endpoint."""
    responses = [(200, "Ok."), (200, "v5.0.5")]
    http = httpx.AsyncClient(
        transport=make_mock_transport(responses),
        base_url="http://qbittorrent.test",
    )
    client = QBittorrentClient(http, username="admin", password="password")

    result = await client.health()

    assert client._authenticated is True
    assert result == QBittorrentHealth(version="v5.0.5")


async def test_health_returns_version() -> None:
    client = make_authenticated_client(status_code=200, body="v5.0.5")

    result = await client.health()

    assert result == QBittorrentHealth(version="v5.0.5")


# ---------------------------------------------------------------------------
# add_torrent()
# ---------------------------------------------------------------------------


async def test_add_torrent_ok() -> None:
    client = make_authenticated_client(status_code=200, body="Ok.")

    result = await client.add_torrent("magnet:?xt=urn:example")

    assert result is None


async def test_add_torrent_fails_body_raises_error() -> None:
    client = make_authenticated_client(status_code=200, body="Fails.")

    with pytest.raises(QBittorrentError):
        await client.add_torrent("magnet:?xt=urn:example")


async def test_add_torrent_passes_form_data() -> None:
    captured_body: bytes = b""

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body
        captured_body = await request.aread()
        return httpx.Response(200, content=b"Ok.")

    http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://qbittorrent.test",
    )
    client = QBittorrentClient(http, username="admin", password="password")
    client._authenticated = True

    await client.add_torrent(
        "magnet:?xt=urn:example",
        category="books",
        save_path="/downloads/books",
    )

    body_str = captured_body.decode()
    assert "urls=" in body_str
    assert "category=books" in body_str
    assert "savepath=" in body_str


# ---------------------------------------------------------------------------
# error translation (against health() with pre-authenticated client)
# ---------------------------------------------------------------------------


async def test_403_raises_forbidden() -> None:
    client = make_authenticated_client(status_code=403, body="")

    with pytest.raises(QBittorrentForbiddenError):
        await client.health()


async def test_500_raises_server_error_after_retries() -> None:
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(500, content=b"internal error")

    http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://qbittorrent.test",
    )
    client = QBittorrentClient(http, username="admin", password="password")
    client._authenticated = True

    with pytest.raises(QBittorrentServerError):
        await client.health()

    assert call_count == 3


async def test_timeout_raises_timeout_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out")

    http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://qbittorrent.test",
    )
    client = QBittorrentClient(http, username="admin", password="password")
    client._authenticated = True

    with pytest.raises(QBittorrentTimeoutError):
        await client.health()


async def test_connect_error_raises_timeout_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://qbittorrent.test",
    )
    client = QBittorrentClient(http, username="admin", password="password")
    client._authenticated = True

    with pytest.raises(QBittorrentTimeoutError):
        await client.health()
