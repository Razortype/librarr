from __future__ import annotations

from collections.abc import AsyncGenerator

import httpx

from app.core.config import settings
from app.integrations.librarr_cloud.client import CloudClient
from app.integrations.openlibrary.client import OpenLibraryClient
from app.integrations.prowlarr.client import ProwlarrClient
from app.services.metadata import MetadataService


async def get_metadata_service() -> AsyncGenerator[MetadataService]:
    """Async generator dependency: yields MetadataService with properly closed httpx clients.

    Per-request clients are intentional for v0.1 simplicity; connection pooling
    becomes relevant at >10 req/s. See docs/FOLLOWUPS.md.
    """
    async with (
        httpx.AsyncClient(
            base_url=settings.openlibrary_base_url,
            timeout=httpx.Timeout(
                settings.http_timeout_read, connect=settings.http_timeout_connect
            ),
        ) as ol_http,
        httpx.AsyncClient(
            base_url=settings.librarr_cloud_url,
            timeout=httpx.Timeout(
                settings.cloud_timeout_read, connect=settings.http_timeout_connect
            ),
        ) as cloud_http,
    ):
        yield MetadataService(
            ol_client=OpenLibraryClient(ol_http),
            cloud_client=CloudClient(cloud_http, api_key=settings.librarr_cloud_api_key),
        )


async def get_prowlarr_client() -> AsyncGenerator[ProwlarrClient]:
    """Async generator dependency: yields ProwlarrClient with a properly closed httpx client.

    Per-request client is intentional for v0.1 simplicity; connection pooling
    becomes relevant at >10 req/s. See docs/FOLLOWUPS.md.
    """
    async with httpx.AsyncClient(
        base_url=settings.prowlarr_url,
        timeout=httpx.Timeout(
            settings.http_timeout_read,
            connect=settings.http_timeout_connect,
        ),
    ) as http:
        yield ProwlarrClient(http, api_key=settings.prowlarr_api_key)
