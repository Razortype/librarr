from __future__ import annotations

import httpx
import structlog

from app.integrations.exceptions import (
    CloudRateLimitError,
    CloudRequestError,
    CloudServerError,
    CloudTimeoutError,
)
from app.integrations.librarr_cloud.schemas import (
    EnrichRequest,
    EnrichStatus,
    FeedbackRequest,
    LookupResponse,
)
from app.schemas.metadata import MetadataResult

logger = structlog.get_logger(__name__)


class CloudClient:
    """Async client for the librarr-cloud metadata enrichment API.

    No tenacity retry — transient errors are handled by the service-layer fallback.
    Raises typed exceptions immediately on first failure (except feedback, which swallows).
    """

    def __init__(self, http_client: httpx.AsyncClient, api_key: str) -> None:
        self._http = http_client
        # Set auth header as safety net regardless of whether caller pre-set it
        self._http.headers.update({"X-Librarr-Key": api_key})
        self._http.event_hooks["response"] = [self._log_response]

    async def _log_response(self, response: httpx.Response) -> None:
        """Async httpx event hook — logs every response at INFO level."""
        try:
            elapsed_ms = round(response.elapsed.total_seconds() * 1000)
        except RuntimeError:
            elapsed_ms = None

        logger.info(
            "cloud_response",
            url=str(response.url),
            status_code=response.status_code,
            duration_ms=elapsed_ms,
        )

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Translate HTTP error status codes to typed exceptions."""
        if response.status_code == 429:
            retry_after_raw = response.headers.get("Retry-After")
            retry_after: int | None = (
                int(retry_after_raw)
                if retry_after_raw and retry_after_raw.isdigit()
                else None
            )
            raise CloudRateLimitError(retry_after=retry_after)
        if 400 <= response.status_code < 500:
            raise CloudRequestError(
                status_code=response.status_code, message=response.text[:200]
            )
        if response.status_code >= 500:
            raise CloudServerError(
                status_code=response.status_code, message=response.text[:200]
            )

    async def enrich_request(self, query: str, entity_type: str) -> EnrichStatus:
        """POST /v1/metadata/enrich.

        Returns immediately with status=pending or status=complete.
        Raises CloudTimeoutError, CloudRateLimitError, CloudRequestError, CloudServerError.
        """
        url = "/v1/metadata/enrich"
        payload = EnrichRequest(query=query, entity_type=entity_type)
        try:
            response = await self._http.post(url, json=payload.model_dump())
        except httpx.TimeoutException as exc:
            logger.warning("cloud_timeout", url=url, error=str(exc))
            raise CloudTimeoutError(str(exc)) from exc

        self._raise_for_status(response)
        return EnrichStatus.model_validate(response.json())

    async def enrich_poll(self, request_id: str) -> EnrichStatus:
        """GET /v1/metadata/enrich/{request_id}.

        Returns current status.
        Raises CloudTimeoutError, CloudRateLimitError, CloudRequestError, CloudServerError.
        """
        url = f"/v1/metadata/enrich/{request_id}"
        try:
            response = await self._http.get(url)
        except httpx.TimeoutException as exc:
            logger.warning("cloud_timeout", url=url, error=str(exc))
            raise CloudTimeoutError(str(exc)) from exc

        self._raise_for_status(response)
        return EnrichStatus.model_validate(response.json())

    async def lookup(self, external_id: str, entity_type: str) -> MetadataResult | None:
        """GET /v1/metadata/lookup.

        Returns None if not in cloud cache.
        Raises CloudTimeoutError, CloudRateLimitError, CloudRequestError, CloudServerError.
        """
        url = "/v1/metadata/lookup"
        try:
            response = await self._http.get(
                url, params={"external_id": external_id, "entity_type": entity_type}
            )
        except httpx.TimeoutException as exc:
            logger.warning("cloud_timeout", url=url, error=str(exc))
            raise CloudTimeoutError(str(exc)) from exc

        self._raise_for_status(response)
        data = LookupResponse.model_validate(response.json())
        return data.result

    async def feedback(
        self,
        request_id: str,
        field: str,
        correct_value: str,
        entity_type: str,
    ) -> None:
        """POST /v1/metadata/feedback.

        Fire-and-forget — logs failure at WARNING, does not raise.
        """
        url = "/v1/metadata/feedback"
        payload = FeedbackRequest(
            request_id=request_id,
            field=field,
            correct_value=correct_value,
            entity_type=entity_type,
        )
        try:
            response = await self._http.post(url, json=payload.model_dump())
            self._raise_for_status(response)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "cloud_feedback_failed",
                request_id=request_id,
                field=field,
                error=str(exc),
            )
