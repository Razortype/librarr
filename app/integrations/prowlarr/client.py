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
    ProwlarrAuthError,
    ProwlarrDownloadError,
    ProwlarrError,
    ProwlarrNotFoundError,
    ProwlarrRateLimitError,
    ProwlarrServerError,
    ProwlarrTimeoutError,
)
from app.integrations.prowlarr.schemas import (
    ProwlarrSearchResultRaw,
    ProwlarrSystemStatusRaw,
)
from app.schemas.prowlarr import ProwlarrHealth, ProwlarrRelease

logger = structlog.get_logger(__name__)

_SEARCH_LIMIT_DEFAULT = 25

_RETRYABLE = (ProwlarrRateLimitError, ProwlarrServerError, ProwlarrTimeoutError)


class ProwlarrClient:
    """Async client for the Prowlarr indexer manager API."""

    def __init__(self, http: httpx.AsyncClient, api_key: str) -> None:
        self._http = http
        self._http.headers["X-Api-Key"] = api_key
        self._http.event_hooks["response"].append(self._log_response)

    async def _log_response(self, response: httpx.Response) -> None:
        try:
            elapsed_ms = round(response.elapsed.total_seconds() * 1000)
        except RuntimeError:
            elapsed_ms = None

        logger.info(
            "prowlarr_response",
            url=str(response.url),
            status_code=response.status_code,
            duration_ms=elapsed_ms,
        )

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code == 401:
            raise ProwlarrAuthError("Prowlarr: invalid or missing API key")
        if response.status_code == 404:
            raise ProwlarrNotFoundError(f"Prowlarr: not found: {response.url}")
        if response.status_code == 429:
            retry_after_raw = response.headers.get("Retry-After")
            retry_after: int | None = (
                int(retry_after_raw) if retry_after_raw and retry_after_raw.isdigit() else None
            )
            raise ProwlarrRateLimitError(retry_after=retry_after)
        if response.status_code >= 500:
            raise ProwlarrServerError(status_code=response.status_code, message=response.text[:200])
        if response.status_code >= 400:
            raise ProwlarrError(f"{response.status_code}: {response.text[:200]}")

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4) + wait_random(0, 0.5),
        reraise=True,
    )
    async def search(self, query: str, limit: int = _SEARCH_LIMIT_DEFAULT) -> list[ProwlarrRelease]:
        """Search all configured Prowlarr indexers and return normalized releases."""
        url = "/api/v1/search"
        try:
            response = await self._http.get(
                url,
                params={"query": query, "type": "search", "limit": limit},
            )
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.warning("prowlarr_timeout", url=url, error=str(exc))
            raise ProwlarrTimeoutError(str(exc)) from exc

        self._raise_for_status(response)

        raws = [ProwlarrSearchResultRaw.model_validate(item) for item in response.json()]
        return [
            ProwlarrRelease(
                guid=r.guid,
                title=r.title,
                indexer_name=r.indexer,
                size_bytes=r.size,
                publish_date=r.publish_date,
                download_url=r.download_url,
                info_url=r.info_url,
                seeders=r.seeders,
                leechers=r.leechers,
                protocol=r.protocol,  # type: ignore[arg-type]  # Literal cast at boundary
            )
            for r in raws
        ]

    async def download_release(self, url: str) -> bytes | str:
        """Fetch a release download URL.

        Returns .torrent bytes on HTTP 200, or a magnet URI string when Prowlarr
        redirects to a magnet: link.  Does not follow redirects so the magnet
        case is detectable.

        Raises:
            ProwlarrTimeoutError: on network timeout.
            ProwlarrDownloadError: on any non-torrent / non-magnet response.
        """
        try:
            response = await self._http.get(url, follow_redirects=False)
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.warning("prowlarr_download_timeout", url=url, error=str(exc))
            raise ProwlarrTimeoutError(str(exc)) from exc

        if response.is_redirect:
            location = response.headers.get("location", "")
            if location.startswith("magnet:"):
                return location
            raise ProwlarrDownloadError(f"Unexpected redirect target: {location[:100]}")

        self._raise_for_status(response)

        if response.status_code == 200:
            return response.content

        raise ProwlarrDownloadError(f"Unexpected status from download URL: {response.status_code}")

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4) + wait_random(0, 0.5),
        reraise=True,
    )
    async def health(self) -> ProwlarrHealth:
        """Fetch Prowlarr system status. Used for test-connection and health checks."""
        url = "/api/v1/system/status"
        try:
            response = await self._http.get(url)
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.warning("prowlarr_timeout", url=url, error=str(exc))
            raise ProwlarrTimeoutError(str(exc)) from exc

        self._raise_for_status(response)

        raw = ProwlarrSystemStatusRaw.model_validate(response.json())
        return ProwlarrHealth(version=raw.version, app_name=raw.app_name)
