from __future__ import annotations

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from app.integrations.exceptions import (
    QBittorrentAuthError,
    QBittorrentError,
    QBittorrentForbiddenError,
    QBittorrentServerError,
    QBittorrentTimeoutError,
)
from app.schemas.qbittorrent import QBittorrentHealth

logger = structlog.get_logger(__name__)

_RETRYABLE = (QBittorrentServerError, QBittorrentTimeoutError)


class QBittorrentClient:
    """Async client for the qBittorrent Web API v2."""

    def __init__(self, http: httpx.AsyncClient, username: str, password: str) -> None:
        self._http = http
        self._username = username
        self._password = password
        self._authenticated = False
        self._http.event_hooks["response"].append(self._log_response)

    async def _log_response(self, response: httpx.Response) -> None:
        try:
            elapsed_ms = round(response.elapsed.total_seconds() * 1000)
        except RuntimeError:
            elapsed_ms = None

        logger.info(
            "qbittorrent_response",
            url=str(response.url),
            status_code=response.status_code,
            duration_ms=elapsed_ms,
        )

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code == 403:
            raise QBittorrentForbiddenError(
                "qBittorrent 403: check 'Server domains' config in qBittorrent"
            )
        if response.status_code >= 500:
            raise QBittorrentServerError(
                status_code=response.status_code, message=response.text[:200]
            )
        if response.status_code >= 400:
            raise QBittorrentError(f"{response.status_code}: {response.text[:200]}")

    async def login(self) -> None:
        """Authenticate with qBittorrent and persist the SID cookie."""
        url = "/api/v2/auth/login"
        try:
            response = await self._http.post(
                url,
                data={"username": self._username, "password": self._password},
            )
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.warning("qbittorrent_timeout", url=url, error=str(exc))
            raise QBittorrentTimeoutError(str(exc)) from exc

        if response.status_code == 403:
            raise QBittorrentForbiddenError(
                "qBittorrent 403: check 'Server domains' config in qBittorrent"
            )
        if response.status_code >= 500:
            raise QBittorrentServerError(
                status_code=response.status_code, message=response.text[:200]
            )
        if response.status_code >= 400:
            raise QBittorrentError(f"{response.status_code}: {response.text[:200]}")

        if response.text.strip() == "Fails.":
            raise QBittorrentAuthError("qBittorrent: invalid username or password")

        self._authenticated = True

    async def _ensure_authenticated(self) -> None:
        if not self._authenticated:
            await self.login()

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4) + wait_random(0, 0.5),
        reraise=True,
    )
    async def health(self) -> QBittorrentHealth:
        """Fetch qBittorrent app version. Used for test-connection."""
        await self._ensure_authenticated()
        url = "/api/v2/app/version"
        try:
            response = await self._http.get(url)
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.warning("qbittorrent_timeout", url=url, error=str(exc))
            raise QBittorrentTimeoutError(str(exc)) from exc

        self._raise_for_status(response)
        return QBittorrentHealth(version=response.text.strip())

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4) + wait_random(0, 0.5),
        reraise=True,
    )
    async def add_torrent(
        self,
        urls: str,
        *,
        category: str | None = None,
        tags: str | None = None,
        save_path: str | None = None,
    ) -> None:
        """Add one or more torrents by URL or magnet to qBittorrent."""
        await self._ensure_authenticated()
        url = "/api/v2/torrents/add"
        data: dict[str, str] = {"urls": urls}
        if category is not None:
            data["category"] = category
        if tags is not None:
            data["tags"] = tags
        if save_path is not None:
            data["savepath"] = save_path

        try:
            response = await self._http.post(url, data=data)
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.warning("qbittorrent_timeout", url=url, error=str(exc))
            raise QBittorrentTimeoutError(str(exc)) from exc

        self._raise_for_status(response)

        if response.text.strip() == "Fails.":
            raise QBittorrentError("qBittorrent: add_torrent failed")

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4) + wait_random(0, 0.5),
        reraise=True,
    )
    async def add_torrent_file(
        self,
        content: bytes,
        *,
        category: str | None = None,
        tags: str | None = None,
    ) -> None:
        """Add a torrent by uploading raw .torrent file bytes to qBittorrent."""
        await self._ensure_authenticated()
        url = "/api/v2/torrents/add"
        data: dict[str, str] = {}
        if category is not None:
            data["category"] = category
        if tags is not None:
            data["tags"] = tags

        try:
            response = await self._http.post(
                url,
                data=data,
                files={"torrents": ("release.torrent", content, "application/x-bittorrent")},
            )
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.warning("qbittorrent_timeout", url=url, error=str(exc))
            raise QBittorrentTimeoutError(str(exc)) from exc

        self._raise_for_status(response)

        if response.text.strip() == "Fails.":
            raise QBittorrentError("qBittorrent: add_torrent_file failed")

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4) + wait_random(0, 0.5),
        reraise=True,
    )
    async def get_torrents(self, *, tag: str | None = None) -> list[dict]:
        """Return torrent info list, optionally filtered by tag."""
        await self._ensure_authenticated()
        url = "/api/v2/torrents/info"
        params: dict[str, str] = {}
        if tag is not None:
            params["tag"] = tag

        try:
            response = await self._http.get(url, params=params)
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.warning("qbittorrent_timeout", url=url, error=str(exc))
            raise QBittorrentTimeoutError(str(exc)) from exc

        self._raise_for_status(response)
        return response.json()
