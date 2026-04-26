from __future__ import annotations

import asyncio
import time

import structlog

from app.core.config import settings
from app.integrations.exceptions import (
    CloudClientError,
    CloudRateLimitError,
    CloudRequestError,
    CloudServerError,
    CloudTimeoutError,
    OLNotFoundError,
)
from app.integrations.librarr_cloud.client import CloudClient
from app.integrations.openlibrary.client import OpenLibraryClient
from app.schemas.metadata import AuthorMetadata, BookMetadata, EditionMetadata, MetadataResult

logger = structlog.get_logger(__name__)


class MetadataService:
    """Orchestrates metadata enrichment: cloud-first with Open Library fallback.

    Cloud enrichment: POST /v1/metadata/enrich has a 5s hard timeout (asyncio.wait_for).
    On pending, polls every 3s with a 30s total budget.
    Any cloud timeout/5xx at any stage triggers immediate OL fallback.
    Total worst-case wait: ~30s before OL fallback.
    Note: for production concurrent use, move polling to an Arq background task
    (see docs/FOLLOWUPS.md).
    """

    def __init__(self, ol_client: OpenLibraryClient, cloud_client: CloudClient) -> None:
        self._ol = ol_client
        self._cloud = cloud_client

    async def search_books(self, title: str, author: str | None = None) -> list[BookMetadata]:
        """Search for books. Tries cloud enrich, falls back to direct OL search."""
        if not settings.librarr_cloud_api_key:
            logger.info("metadata_cloud_skip", reason="no_api_key", method="search_books")
            return await self._ol.search_books(title=title, author=author)

        query = f"{title} {author}".strip() if author else title
        result = await self._cloud_enrich_with_poll(query=query, entity_type="book")

        if result is not None:
            logger.info("metadata_cloud_hit", method="search_books", query=query)
            # Cloud returned a single enriched result; wrap in list
            if isinstance(result, BookMetadata):
                return [result]
            # Unexpected type from cloud — fall through to OL
            logger.warning(
                "metadata_cloud_unexpected_type",
                method="search_books",
                result_type=type(result).__name__,
            )

        logger.info("metadata_ol_fallback", method="search_books", query=query)
        return await self._ol.search_books(title=title, author=author)

    async def lookup_by_isbn(self, isbn: str) -> EditionMetadata | None:
        """Lookup edition by ISBN. Tries cloud lookup, falls back to direct OL."""
        if not settings.librarr_cloud_api_key:
            logger.info("metadata_cloud_skip", reason="no_api_key", method="lookup_by_isbn")
            return await self._ol_lookup_by_isbn_safe(isbn)

        try:
            result = await self._cloud.lookup(
                external_id=f"isbn:{isbn}", entity_type="edition"
            )
        except (CloudTimeoutError, CloudServerError, CloudRateLimitError, CloudRequestError) as exc:
            logger.info(
                "metadata_ol_fallback",
                method="lookup_by_isbn",
                isbn=isbn,
                reason=type(exc).__name__,
            )
            return await self._ol_lookup_by_isbn_safe(isbn)
        except CloudClientError as exc:
            logger.warning(
                "metadata_cloud_unexpected_error",
                method="lookup_by_isbn",
                isbn=isbn,
                error=str(exc),
            )
            return await self._ol_lookup_by_isbn_safe(isbn)

        if result is not None:
            logger.info("metadata_cloud_hit", method="lookup_by_isbn", isbn=isbn)
            if isinstance(result, EditionMetadata):
                return result
            logger.warning(
                "metadata_cloud_unexpected_type",
                method="lookup_by_isbn",
                result_type=type(result).__name__,
            )

        logger.info("metadata_ol_fallback", method="lookup_by_isbn", isbn=isbn, reason="cache_miss")
        return await self._ol_lookup_by_isbn_safe(isbn)

    async def lookup_author(self, ol_author_id: str) -> AuthorMetadata | None:
        """Lookup author by OL ID. Direct OL only (no cloud lookup for authors by ID)."""
        try:
            return await self._ol.lookup_author(ol_author_id)
        except OLNotFoundError:
            return None

    async def _cloud_enrich_with_poll(
        self, query: str, entity_type: str
    ) -> MetadataResult | None:
        """Attempt cloud enrichment with polling. Returns None to signal fallback needed."""
        # Step 1: initial POST with 5s hard timeout
        try:
            status = await asyncio.wait_for(
                self._cloud.enrich_request(query=query, entity_type=entity_type),
                timeout=5.0,
            )
        except TimeoutError:
            logger.info(
                "metadata_ol_fallback",
                reason="cloud_initial_timeout",
                query=query,
                entity_type=entity_type,
            )
            return None
        except (CloudTimeoutError, CloudServerError):
            logger.info(
                "metadata_ol_fallback",
                reason="cloud_initial_error",
                query=query,
                entity_type=entity_type,
            )
            return None
        except CloudRateLimitError:
            logger.info(
                "metadata_ol_fallback",
                reason="cloud_rate_limited",
                query=query,
                entity_type=entity_type,
            )
            return None
        except CloudRequestError as exc:
            logger.warning(
                "metadata_cloud_request_error",
                query=query,
                entity_type=entity_type,
                error=str(exc),
            )
            logger.info(
                "metadata_ol_fallback",
                reason="cloud_request_error",
                query=query,
                entity_type=entity_type,
            )
            return None

        if status.status == "complete":
            return status.result

        # Step 2: polling loop — total 30s budget
        request_id = status.request_id
        poll_deadline = time.monotonic() + 30.0

        while time.monotonic() < poll_deadline:
            await asyncio.sleep(3.0)

            try:
                status = await self._cloud.enrich_poll(request_id=request_id)
            except (CloudServerError, CloudTimeoutError):
                logger.info(
                    "metadata_ol_fallback",
                    reason="cloud_poll_error",
                    request_id=request_id,
                    query=query,
                    entity_type=entity_type,
                )
                return None
            except CloudRateLimitError:
                logger.info(
                    "metadata_ol_fallback",
                    reason="cloud_poll_rate_limited",
                    request_id=request_id,
                    query=query,
                    entity_type=entity_type,
                )
                return None

            if status.status == "complete":
                return status.result

        # Polling budget exhausted
        logger.info(
            "metadata_ol_fallback",
            reason="cloud_poll_budget_exhausted",
            request_id=request_id,
            query=query,
            entity_type=entity_type,
        )
        return None

    async def _ol_lookup_by_isbn_safe(self, isbn: str) -> EditionMetadata | None:
        """Call OL lookup_by_isbn; return None on OLNotFoundError."""
        try:
            return await self._ol.lookup_by_isbn(isbn)
        except OLNotFoundError:
            return None
