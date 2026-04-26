from __future__ import annotations

import re
import time
from datetime import date, datetime

import httpx
import structlog
from dateutil import parser as dateutil_parser
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from app.integrations.exceptions import (
    OLNotFoundError,
    OLRateLimitError,
    OLServerError,
    OLTimeoutError,
)
from app.integrations.openlibrary.schemas import (
    OLAuthorResponse,
    OLEditionResponse,
    OLSearchDoc,
    OLSearchResponse,
    OLWorkResponse,
)
from app.schemas.metadata import AuthorMetadata, AuthorStub, BookMetadata, EditionMetadata

logger = structlog.get_logger(__name__)

_LANG_MAP: dict[str, str] = {
    "eng": "en",
    "fre": "fr",
    "ger": "de",
    "spa": "es",
    "ita": "it",
    "por": "pt",
    "rus": "ru",
    "chi": "zh",
    "jpn": "ja",
    "ara": "ar",
    "hin": "hi",
    "dut": "nl",
    "pol": "pl",
    "swe": "sv",
    "nor": "no",
    "dan": "da",
    "fin": "fi",
    "tur": "tr",
    "kor": "ko",
    "heb": "he",
}


def _strip_ol_key(key: str) -> str:
    """Strip OL path prefix: '/works/OL123W' -> 'OL123W'."""
    return key.rsplit("/", 1)[-1]


def _map_language_code(code: str) -> str | None:
    """Map OL 3-letter language code to ISO 639-1 2-letter code."""
    return _LANG_MAP.get(code.lower())


def _map_physical_format(fmt: str) -> str | None:
    """Map OL physical format string to EditionFormat enum value.

    Uses case-insensitive substring matching.
    """
    lower = fmt.lower()
    if "mass market" in lower:
        return "mass_market"
    if "large print" in lower:
        return "large_print"
    if "audio" in lower:
        return "audiobook"
    if "kindle" in lower or "ebook" in lower or "epub" in lower or "digital" in lower:
        return "ebook"
    if "hardcover" in lower or "hard cover" in lower or "hardback" in lower:
        return "hardcover"
    if "paperback" in lower or "trade paper" in lower:
        return "paperback"
    return None


class OpenLibraryClient:
    """Async client for the Open Library API with tenacity retry and structlog logging."""

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http = http_client
        self._http.event_hooks["response"].append(self._log_response)

    async def _log_response(self, response: httpx.Response) -> None:
        """Async httpx event hook — logs every response at INFO level."""
        # elapsed is available after response.aread() / stream consumed, but for event hooks
        # it may not be set yet; fall back gracefully.
        try:
            elapsed_ms = round(response.elapsed.total_seconds() * 1000)
        except RuntimeError:
            elapsed_ms = None

        logger.info(
            "openlibrary_response",
            url=str(response.url),
            status_code=response.status_code,
            duration_ms=elapsed_ms,
        )

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Translate HTTP error status codes to typed exceptions."""
        if response.status_code == 404:
            raise OLNotFoundError(f"Not found: {response.url}")
        if response.status_code == 429:
            retry_after_raw = response.headers.get("Retry-After")
            retry_after: int | None = (
                int(retry_after_raw)
                if retry_after_raw and retry_after_raw.isdigit()
                else None
            )
            raise OLRateLimitError(retry_after=retry_after)
        if response.status_code >= 500:
            raise OLServerError(status_code=response.status_code, message=response.text[:200])

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, OLServerError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8) + wait_random(0, 0.5),
        reraise=True,
    )
    async def search_books(
        self, title: str, author: str | None = None, limit: int = 10
    ) -> list[BookMetadata]:
        """Search OL /search.json.

        Returns search-quality data (no description, no full edition detail).
        """
        params: dict[str, str | int] = {"title": title, "limit": limit, "fields": "*"}
        if author:
            params["author"] = author

        url = "/search.json"
        start = time.monotonic()
        try:
            response = await self._http.get(url, params=params)
        except httpx.TimeoutException as exc:
            logger.warning("openlibrary_timeout", url=url, error=str(exc))
            raise OLTimeoutError(str(exc)) from exc

        self._raise_for_status(response)

        duration_ms = round((time.monotonic() - start) * 1000)
        logger.info(
            "openlibrary_search_books",
            title=title,
            author=author,
            limit=limit,
            duration_ms=duration_ms,
        )

        data = OLSearchResponse.model_validate(response.json())
        return [self._normalize_search_doc(doc) for doc in data.docs]

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, OLServerError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8) + wait_random(0, 0.5),
        reraise=True,
    )
    async def lookup_by_isbn(self, isbn: str) -> EditionMetadata:
        """Lookup OL /isbn/{isbn}.json. Raises OLNotFoundError if not found."""
        url = f"/isbn/{isbn}.json"
        start = time.monotonic()
        try:
            response = await self._http.get(url)
        except httpx.TimeoutException as exc:
            logger.warning("openlibrary_timeout", url=url, error=str(exc))
            raise OLTimeoutError(str(exc)) from exc

        self._raise_for_status(response)

        duration_ms = round((time.monotonic() - start) * 1000)
        logger.info("openlibrary_lookup_by_isbn", isbn=isbn, duration_ms=duration_ms)

        data = OLEditionResponse.model_validate(response.json())
        return self._normalize_edition(data)

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, OLServerError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8) + wait_random(0, 0.5),
        reraise=True,
    )
    async def lookup_work(self, ol_work_id: str) -> BookMetadata:
        """Lookup OL /works/{ol_work_id}.json. Returns full work detail including description."""
        url = f"/works/{ol_work_id}.json"
        start = time.monotonic()
        try:
            response = await self._http.get(url)
        except httpx.TimeoutException as exc:
            logger.warning("openlibrary_timeout", url=url, error=str(exc))
            raise OLTimeoutError(str(exc)) from exc

        self._raise_for_status(response)

        duration_ms = round((time.monotonic() - start) * 1000)
        logger.info("openlibrary_lookup_work", ol_work_id=ol_work_id, duration_ms=duration_ms)

        data = OLWorkResponse.model_validate(response.json())
        return self._normalize_work(data)

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, OLServerError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8) + wait_random(0, 0.5),
        reraise=True,
    )
    async def lookup_author(self, ol_author_id: str) -> AuthorMetadata:
        """Lookup OL /authors/{ol_author_id}.json."""
        url = f"/authors/{ol_author_id}.json"
        start = time.monotonic()
        try:
            response = await self._http.get(url)
        except httpx.TimeoutException as exc:
            logger.warning("openlibrary_timeout", url=url, error=str(exc))
            raise OLTimeoutError(str(exc)) from exc

        self._raise_for_status(response)

        duration_ms = round((time.monotonic() - start) * 1000)
        logger.info("openlibrary_lookup_author", ol_author_id=ol_author_id, duration_ms=duration_ms)

        data = OLAuthorResponse.model_validate(response.json())
        return self._normalize_author(data)

    def _normalize_search_doc(self, doc: OLSearchDoc) -> BookMetadata:
        """Normalize an OL search result document into a BookMetadata schema."""
        ol_work_id = _strip_ol_key(doc.key)

        # Build authors by zipping keys and names (zip stops at shortest)
        authors: list[AuthorStub] = []
        keys = doc.author_key or []
        names = doc.author_name or []
        for key, name in zip(keys, names):
            authors.append(AuthorStub(ol_id=_strip_ol_key(key), name=name))
        # If names exist but keys don't (or keys ran out), append remaining names without an id
        if len(names) > len(keys):
            for name in names[len(keys):]:
                authors.append(AuthorStub(ol_id=None, name=name))

        # Detect ISBNs by digit-only length
        isbn_10: str | None = None
        isbn_13: str | None = None
        for raw_isbn in (doc.isbn or []):
            digits = re.sub(r"\D", "", raw_isbn)
            if isbn_10 is None and len(digits) == 10:
                isbn_10 = digits
            elif isbn_13 is None and len(digits) == 13:
                isbn_13 = digits
            if isbn_10 and isbn_13:
                break

        cover_url: str | None = None
        if doc.cover_i is not None:
            cover_url = f"https://covers.openlibrary.org/b/id/{doc.cover_i}-L.jpg"

        original_language: str | None = None
        if doc.language:
            original_language = _map_language_code(doc.language[0])

        return BookMetadata(
            ol_work_id=ol_work_id,
            title=doc.title,
            original_language=original_language,
            publication_year=doc.first_publish_year,
            description=None,
            authors=authors,
            series_names=doc.series,
            cover_url=cover_url,
            external_ids={"openlibrary_work": ol_work_id},
            system_confidence=0.6,
        )

    def _normalize_work(self, data: OLWorkResponse) -> BookMetadata:
        """Normalize an OL work response into a BookMetadata schema."""
        ol_work_id = _strip_ol_key(data.key)

        description: str | None = None
        if isinstance(data.description, str):
            description = data.description
        elif isinstance(data.description, dict):
            description = data.description.get("value")

        return BookMetadata(
            ol_work_id=ol_work_id,
            title=data.title,
            original_language=None,
            publication_year=None,
            description=description,
            authors=[],
            series_names=None,
            cover_url=None,
            external_ids={"openlibrary_work": ol_work_id},
            system_confidence=0.6,
        )

    def _normalize_author(self, data: OLAuthorResponse) -> AuthorMetadata:
        """Normalize an OL author response into an AuthorMetadata schema."""
        ol_id = _strip_ol_key(data.key)

        biography: str | None = None
        if isinstance(data.bio, str):
            biography = data.bio
        elif isinstance(data.bio, dict):
            biography = data.bio.get("value")

        birth_year: int | None = None
        if data.birth_date:
            match = re.search(r"\d{4}", data.birth_date)
            if match:
                birth_year = int(match.group())

        death_year: int | None = None
        if data.death_date:
            match = re.search(r"\d{4}", data.death_date)
            if match:
                death_year = int(match.group())

        image_url: str | None = None
        if data.photos:
            image_url = f"https://covers.openlibrary.org/a/id/{data.photos[0]}-L.jpg"

        return AuthorMetadata(
            ol_id=ol_id,
            name=data.name,
            alternate_names=data.alternate_names,
            birth_year=birth_year,
            death_year=death_year,
            biography=biography,
            image_url=image_url,
            external_ids={"openlibrary_author": ol_id},
            system_confidence=0.6,
        )

    def _normalize_edition(self, data: OLEditionResponse) -> EditionMetadata:
        """Normalize an OL edition response into an EditionMetadata schema."""
        ol_edition_id = _strip_ol_key(data.key)

        ol_work_id: str | None = None
        if data.works:
            ol_work_id = _strip_ol_key(data.works[0]["key"])

        isbn_10: str | None = data.isbn_10[0] if data.isbn_10 else None
        isbn_13: str | None = data.isbn_13[0] if data.isbn_13 else None
        publisher: str | None = data.publishers[0] if data.publishers else None

        publication_date: date | None = None
        if data.publish_date:
            try:
                publication_date = dateutil_parser.parse(
                    data.publish_date, default=datetime(1, 1, 1)
                ).date()
            except (ValueError, OverflowError):
                year_match = re.search(r"\d{4}", data.publish_date)
                if year_match:
                    publication_date = date(int(year_match.group()), 1, 1)

        language: str | None = None
        if data.languages:
            raw_lang_key = data.languages[0].get("key", "")
            lang_code = raw_lang_key.rsplit("/", 1)[-1]
            if lang_code:
                language = _map_language_code(lang_code)

        edition_format: str | None = None
        if data.physical_format:
            edition_format = _map_physical_format(data.physical_format)

        cover_url: str | None = None
        if data.covers:
            cover_url = f"https://covers.openlibrary.org/b/id/{data.covers[0]}-L.jpg"

        external_ids: dict[str, str] = {"openlibrary_edition": ol_edition_id}
        if ol_work_id:
            external_ids["openlibrary_work"] = ol_work_id

        return EditionMetadata(
            ol_edition_id=ol_edition_id,
            ol_work_id=ol_work_id,
            isbn_10=isbn_10,
            isbn_13=isbn_13,
            title=data.title,
            publisher=publisher,
            publication_date=publication_date,
            page_count=data.number_of_pages,
            language=language,
            format=edition_format,
            cover_url=cover_url,
            external_ids=external_ids,
            system_confidence=0.6,
        )
