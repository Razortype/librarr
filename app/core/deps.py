from __future__ import annotations

import httpx

from app.core.config import settings
from app.integrations.librarr_cloud.client import CloudClient
from app.integrations.openlibrary.client import OpenLibraryClient
from app.services.metadata import MetadataService


def get_metadata_service() -> MetadataService:
    """Per-request factory for MetadataService with fresh httpx clients.

    Per-request clients are intentional for v0.1 simplicity; connection pooling
    becomes relevant at >10 req/s. See docs/FOLLOWUPS.md.
    """
    ol_http = httpx.AsyncClient(
        base_url=settings.openlibrary_base_url,
        timeout=httpx.Timeout(
            connect=settings.http_timeout_connect,
            read=settings.http_timeout_read,
        ),
    )
    cloud_http = httpx.AsyncClient(
        base_url=settings.librarr_cloud_url,
        timeout=httpx.Timeout(
            connect=settings.http_timeout_connect,
            read=settings.cloud_timeout_read,
        ),
    )
    return MetadataService(
        ol_client=OpenLibraryClient(ol_http),
        cloud_client=CloudClient(cloud_http, api_key=settings.librarr_cloud_api_key),
    )
