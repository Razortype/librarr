from __future__ import annotations

import uuid

import httpx

from app.schemas.metadata import AuthorStub, BookMetadata, EditionMetadata

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TITLE_PAYLOAD = {"lookup_type": "title_author", "title": "Dune", "author": "Herbert"}
_ISBN_PAYLOAD = {"lookup_type": "isbn", "isbn": "9780385121675"}


def _title(t: str) -> dict:
    return {"lookup_type": "title_author", "title": t}


def _book_meta(
    title: str,
    *,
    ol_id: str = "OL999A",
    author: str = "Test Author",
    description: str | None = "A test description.",
    publication_year: int | None = 2020,
    confidence: float = 0.8,
) -> BookMetadata:
    return BookMetadata(
        ol_work_id="OL12345W",
        title=title,
        original_language="en",
        publication_year=publication_year,
        description=description,
        authors=[AuthorStub(ol_id=ol_id, name=author)],
        cover_url=None,
        external_ids={"openlibrary_work": "OL12345W"},
        system_confidence=confidence,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/book
# ---------------------------------------------------------------------------


async def test_add_book_invalid_input(api_client: httpx.AsyncClient) -> None:
    """Discriminated union rejects missing lookup_type with 422."""
    r = await api_client.post("/api/v1/book", json={"title": "Dune"})
    assert r.status_code == 422
    body = r.json()
    # FastAPI puts discriminator errors in detail
    assert "lookup_type" in str(body)


async def test_add_book_by_title(api_client: httpx.AsyncClient) -> None:
    r = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    assert r.status_code == 201
    body = r.json()
    assert body["metadata_status"] == "resolved"
    assert body["warnings"] == []
    book = body["book"]
    assert book["title"] == "Dune"
    assert book["status"] == "wanted"
    assert book["publication_year"] == 2020
    assert book["description"] == "A test description."
    assert len(book["authors"]) == 1
    assert book["authors"][0]["role"] == "primary"
    assert book["authors"][0]["canonical_name"] == "Test Author"
    assert book["effective_confidence"] == 0.8


async def test_add_book_by_isbn(api_client: httpx.AsyncClient) -> None:
    r = await api_client.post("/api/v1/book", json=_ISBN_PAYLOAD)
    assert r.status_code == 201
    body = r.json()
    assert body["metadata_status"] == "resolved"
    book = body["book"]
    assert len(book["editions"]) == 1
    edition = book["editions"][0]
    assert edition["isbn_13"] == "9780385121675"
    assert edition["format"] == "paperback"
    assert len(book["authors"]) == 1


async def test_add_book_duplicate_isbn(api_client: httpx.AsyncClient) -> None:
    r1 = await api_client.post("/api/v1/book", json=_ISBN_PAYLOAD)
    assert r1.status_code == 201
    existing_id = r1.json()["book"]["id"]

    r2 = await api_client.post("/api/v1/book", json=_ISBN_PAYLOAD)
    assert r2.status_code == 409
    body = r2.json()
    assert body["error"] == "conflict"
    assert body["details"]["existing_book_id"] == existing_id
    assert body["details"]["isbn"] == "9780385121675"


async def test_add_book_metadata_unavailable(
    api_client: httpx.AsyncClient, mock_metadata_service: object
) -> None:
    mock_metadata_service.fail = True  # type: ignore[attr-defined]
    r = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    assert r.status_code == 201
    body = r.json()
    assert body["metadata_status"] == "unresolved"
    assert len(body["warnings"]) >= 1
    assert body["book"]["effective_confidence"] == 0.0


async def test_add_book_title_author_with_unknown_fallback(api_client: httpx.AsyncClient) -> None:
    """Backend must accept author='Unknown', the frontend fallback for empty authors[]."""
    r = await api_client.post(
        "/api/v1/book",
        json={"lookup_type": "title_author", "title": "Orphan Title", "author": "Unknown"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["book"]["title"] == "Orphan Title"
    assert body["book"]["status"] == "wanted"
    assert body["metadata_status"] == "resolved"


async def test_add_book_isbn_no_work_enrichment(
    api_client: httpx.AsyncClient, mock_metadata_service: object
) -> None:
    """ISBN lookup where edition has no ol_work_id skips work enrichment; book still persists."""
    mock_metadata_service.isbn_result = EditionMetadata(  # type: ignore[attr-defined]
        title="Edition Without Work",
        isbn_13="9781234567890",
        system_confidence=0.6,
    )
    r = await api_client.post("/api/v1/book", json={"lookup_type": "isbn", "isbn": "9781234567890"})
    assert r.status_code == 201
    body = r.json()
    assert body["metadata_status"] == "partial"  # confidence 0.6 < 0.7
    assert body["warnings"] == []
    book = body["book"]
    assert book["description"] is None
    assert len(book["editions"]) == 1
    assert book["editions"][0]["isbn_13"] == "9781234567890"


# ---------------------------------------------------------------------------
# GET /api/v1/book (list)
# ---------------------------------------------------------------------------


async def test_list_books_empty(api_client: httpx.AsyncClient) -> None:
    r = await api_client.get("/api/v1/book")
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["limit"] == 50
    assert body["offset"] == 0


async def test_list_books_filter_status(
    api_client: httpx.AsyncClient, mock_metadata_service: object
) -> None:
    # Add two books — both start as "wanted"
    await api_client.post("/api/v1/book", json=_title("Book A"))
    r2 = await api_client.post("/api/v1/book", json=_title("Book B"))
    book_b_id = r2.json()["book"]["id"]

    # Move book B to monitored
    await api_client.patch(f"/api/v1/book/{book_b_id}", json={"status": "monitored"})

    r_wanted = await api_client.get("/api/v1/book?status=wanted")
    assert r_wanted.json()["total"] == 1
    assert r_wanted.json()["items"][0]["title"] == "Book A"

    r_monitored = await api_client.get("/api/v1/book?status=monitored")
    assert r_monitored.json()["total"] == 1
    assert r_monitored.json()["items"][0]["title"] == "Book B"


async def test_list_books_filter_monitored(
    api_client: httpx.AsyncClient, mock_metadata_service: object
) -> None:
    await api_client.post("/api/v1/book", json=_title("Active"))
    r2 = await api_client.post("/api/v1/book", json=_title("Passive"))
    passive_id = r2.json()["book"]["id"]

    # Move "Passive" to unmonitored
    await api_client.patch(f"/api/v1/book/{passive_id}", json={"status": "unmonitored"})

    r = await api_client.get("/api/v1/book?monitored=true")
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["title"] == "Active"

    r2 = await api_client.get("/api/v1/book?monitored=false")
    assert r2.json()["total"] == 1
    assert r2.json()["items"][0]["title"] == "Passive"


async def test_list_books_filter_author_id(
    api_client: httpx.AsyncClient, mock_metadata_service: object
) -> None:
    # Book 1 with default author (OL999A "Test Author")
    r1 = await api_client.post("/api/v1/book", json=_title("Book One"))
    assert r1.status_code == 201
    book1_author_id = r1.json()["book"]["authors"][0]["id"]

    # Book 2 with different author
    mock_metadata_service.search_results = [  # type: ignore[attr-defined]
        _book_meta("Book Two", ol_id="OL888A", author="Other Author")
    ]
    r2 = await api_client.post("/api/v1/book", json=_title("Book Two"))
    assert r2.status_code == 201

    r = await api_client.get(f"/api/v1/book?author_id={book1_author_id}")
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["title"] == "Book One"


async def test_list_books_sort_title(
    api_client: httpx.AsyncClient, mock_metadata_service: object
) -> None:
    for title in ("Zoo", "Apple", "Middle"):
        mock_metadata_service.search_results = [_book_meta(title)]  # type: ignore[attr-defined]
        await api_client.post("/api/v1/book", json=_title(title))

    r_asc = await api_client.get("/api/v1/book?sort_key=title&sort_dir=asc")
    titles_asc = [b["title"] for b in r_asc.json()["items"]]
    assert titles_asc == ["Apple", "Middle", "Zoo"]

    r_desc = await api_client.get("/api/v1/book?sort_key=title&sort_dir=desc")
    titles_desc = [b["title"] for b in r_desc.json()["items"]]
    assert titles_desc == ["Zoo", "Middle", "Apple"]


async def test_list_books_pagination(
    api_client: httpx.AsyncClient, mock_metadata_service: object
) -> None:
    for i in range(5):
        mock_metadata_service.search_results = [_book_meta(f"Book {i:02d}")]  # type: ignore[attr-defined]
        await api_client.post("/api/v1/book", json=_title(f"Book {i:02d}"))

    r = await api_client.get("/api/v1/book?limit=2&offset=2&sort_key=title&sort_dir=asc")
    body = r.json()
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 2
    assert len(body["items"]) == 2
    assert body["items"][0]["title"] == "Book 02"
    assert body["items"][1]["title"] == "Book 03"


async def test_pagination_bounds(api_client: httpx.AsyncClient) -> None:
    # limit > 200 → 422
    r = await api_client.get("/api/v1/book?limit=300")
    assert r.status_code == 422

    # limit = 0 → 422 (ge=1)
    r = await api_client.get("/api/v1/book?limit=0")
    assert r.status_code == 422

    # offset beyond dataset → empty items, correct total
    await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    await api_client.post("/api/v1/book", json=_title("Other Book"))
    r = await api_client.get("/api/v1/book?offset=999")
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["total"] == 2


# ---------------------------------------------------------------------------
# GET /api/v1/book/{id}
# ---------------------------------------------------------------------------


async def test_get_book_detail(api_client: httpx.AsyncClient) -> None:
    r_add = await api_client.post("/api/v1/book", json=_ISBN_PAYLOAD)
    book_id = r_add.json()["book"]["id"]

    r = await api_client.get(f"/api/v1/book/{book_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == book_id
    assert len(body["editions"]) == 1
    assert len(body["authors"]) == 1
    assert body["authors"][0]["role"] == "primary"
    # All confidence fields present
    assert "system_confidence" in body
    assert "user_confidence" in body
    assert "effective_confidence" in body


async def test_get_book_not_found(api_client: httpx.AsyncClient) -> None:
    r = await api_client.get(f"/api/v1/book/{uuid.uuid4()}")
    assert r.status_code == 404
    body = r.json()
    assert body["error"] == "not_found"
    assert "book_id" in body["details"]


# ---------------------------------------------------------------------------
# PATCH /api/v1/book/{id}
# ---------------------------------------------------------------------------


async def test_patch_book_status_only(api_client: httpx.AsyncClient) -> None:
    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    book_id = r_add.json()["book"]["id"]

    r = await api_client.patch(f"/api/v1/book/{book_id}", json={"status": "monitored"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "monitored"
    # Status-only patch must not touch confidence
    assert body["user_confidence"] is None


async def test_patch_book_metadata_field(api_client: httpx.AsyncClient) -> None:
    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    book_id = r_add.json()["book"]["id"]

    r = await api_client.patch(f"/api/v1/book/{book_id}", json={"title": "New Title"})
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "New Title"
    assert body["user_confidence"] == 1.0
    assert body["effective_confidence"] == 1.0


async def test_patch_book_partial_metadata_only_bumps_touched(
    api_client: httpx.AsyncClient,
) -> None:
    """Mixed patch: metadata field + operational field → confidence bumped."""
    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    book_id = r_add.json()["book"]["id"]

    r = await api_client.patch(
        f"/api/v1/book/{book_id}",
        json={"title": "Updated Title", "status": "monitored"},
    )
    assert r.status_code == 200
    body = r.json()
    # Both fields applied
    assert body["title"] == "Updated Title"
    assert body["status"] == "monitored"
    # Metadata field was in the patch → user_confidence = 1.0
    assert body["user_confidence"] == 1.0


async def test_patch_book_not_found(api_client: httpx.AsyncClient) -> None:
    r = await api_client.patch(f"/api/v1/book/{uuid.uuid4()}", json={"status": "monitored"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/v1/book/{id}
# ---------------------------------------------------------------------------


async def test_soft_delete_book(api_client: httpx.AsyncClient) -> None:
    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    book_id = r_add.json()["book"]["id"]

    r = await api_client.delete(f"/api/v1/book/{book_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["archived"] is True
    assert body["deleted"] is False
    assert body["id"] == book_id

    # Book still exists but is archived
    r_get = await api_client.get(f"/api/v1/book/{book_id}")
    assert r_get.status_code == 200
    assert r_get.json()["status"] == "archived"


async def test_hard_delete_book(api_client: httpx.AsyncClient) -> None:
    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    book_id = r_add.json()["book"]["id"]

    r = await api_client.delete(f"/api/v1/book/{book_id}?hard=true")
    assert r.status_code == 200
    body = r.json()
    assert body["deleted"] is True
    assert body["id"] == book_id

    # Book is gone
    r_get = await api_client.get(f"/api/v1/book/{book_id}")
    assert r_get.status_code == 404


async def test_delete_book_not_found(api_client: httpx.AsyncClient) -> None:
    r = await api_client.delete(f"/api/v1/book/{uuid.uuid4()}")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Author dedup
# ---------------------------------------------------------------------------


async def test_author_dedup(api_client: httpx.AsyncClient, mock_metadata_service: object) -> None:
    """Two books with same OL author ID → one author row, both books linked."""
    r1 = await api_client.post("/api/v1/book", json=_title("Book One"))
    r2 = await api_client.post("/api/v1/book", json=_title("Book Two"))
    assert r1.status_code == r2.status_code == 201

    author_id_1 = r1.json()["book"]["authors"][0]["id"]
    author_id_2 = r2.json()["book"]["authors"][0]["id"]
    assert author_id_1 == author_id_2, "Same OL ID must reuse existing author"

    r_books = await api_client.get(f"/api/v1/author/{author_id_1}/book")
    assert r_books.json()["total"] == 2


async def test_add_book_with_existing_author_merges_external_ids(
    api_client: httpx.AsyncClient,
    mock_metadata_service: object,
    db_session: object,
) -> None:
    """merge_external_ids preserves pre-existing keys on the author row."""
    # Add first book → author created with openlibrary_author: OL999A
    r1 = await api_client.post("/api/v1/book", json=_title("Book One"))
    assert r1.status_code == 201
    author_id = r1.json()["book"]["authors"][0]["id"]

    # Inject a synthetic external ID directly into the DB (simulates a future source)
    from app.models.author import Author as AuthorModel

    author_obj = await db_session.get(AuthorModel, uuid.UUID(author_id))  # type: ignore[union-attr]
    author_obj.external_ids = {**author_obj.external_ids, "synthetic_source": "S1"}
    await db_session.commit()  # type: ignore[union-attr]

    # Add second book — same mock, same OL author ID
    r2 = await api_client.post("/api/v1/book", json=_title("Book Two"))
    assert r2.status_code == 201
    assert r2.json()["book"]["authors"][0]["id"] == author_id

    # Synthetic key must survive the merge
    r_author = await api_client.get(f"/api/v1/author/{author_id}")
    assert r_author.status_code == 200
    ext_ids = r_author.json()["external_ids"]
    assert ext_ids.get("synthetic_source") == "S1", "merge_external_ids must not drop existing keys"
    assert "openlibrary_author" in ext_ids


# ---------------------------------------------------------------------------
# GET /api/v1/author/{id}
# ---------------------------------------------------------------------------


async def test_get_author(api_client: httpx.AsyncClient) -> None:
    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    author_id = r_add.json()["book"]["authors"][0]["id"]

    r = await api_client.get(f"/api/v1/author/{author_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == author_id
    assert body["canonical_name"] == "Test Author"
    assert "effective_confidence" in body
    # books field is None for the plain detail endpoint (books sub-resource is separate)
    assert body["books"] is None


async def test_get_author_books(api_client: httpx.AsyncClient) -> None:
    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    author_id = r_add.json()["book"]["authors"][0]["id"]

    r = await api_client.get(f"/api/v1/author/{author_id}/book")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Dune"


async def test_get_author_not_found(api_client: httpx.AsyncClient) -> None:
    r = await api_client.get(f"/api/v1/author/{uuid.uuid4()}")
    assert r.status_code == 404
    assert r.json()["error"] == "not_found"


# ---------------------------------------------------------------------------
# POST /api/v1/command
# ---------------------------------------------------------------------------


async def test_command_refresh_book_metadata_resolved(
    api_client: httpx.AsyncClient, mock_metadata_service: object
) -> None:
    """Refresh fills in empty fields from metadata service."""
    # Add book with sparse metadata (no description or year)
    mock_metadata_service.search_results = [  # type: ignore[attr-defined]
        _book_meta("Sparse", description=None, publication_year=None, confidence=0.5)
    ]
    r_add = await api_client.post("/api/v1/book", json=_title("Sparse"))
    assert r_add.status_code == 201
    book_id = r_add.json()["book"]["id"]
    assert r_add.json()["book"]["description"] is None
    assert r_add.json()["book"]["publication_year"] is None

    # Reset mock to default (full metadata)
    mock_metadata_service.search_results = None  # type: ignore[attr-defined]

    r_cmd = await api_client.post(
        "/api/v1/command",
        json={"name": "RefreshBook", "body": {"bookId": book_id}},
    )
    assert r_cmd.status_code == 201
    assert r_cmd.json()["status"] == "completed"
    assert r_cmd.json()["name"] == "RefreshBook"

    r_get = await api_client.get(f"/api/v1/book/{book_id}")
    book = r_get.json()
    assert book["description"] == "A test description."
    assert book["publication_year"] == 2020
    assert book["system_confidence"] == 0.8  # updated from 0.5


async def test_command_refresh_book_no_changes(api_client: httpx.AsyncClient) -> None:
    """Refresh on fully-populated book is idempotent."""
    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    assert r_add.status_code == 201
    book_id = r_add.json()["book"]["id"]
    original_desc = r_add.json()["book"]["description"]
    original_conf = r_add.json()["book"]["system_confidence"]

    r_cmd = await api_client.post(
        "/api/v1/command",
        json={"name": "RefreshBook", "body": {"bookId": book_id}},
    )
    assert r_cmd.status_code == 201
    assert r_cmd.json()["status"] == "completed"

    r_get = await api_client.get(f"/api/v1/book/{book_id}")
    assert r_get.json()["description"] == original_desc
    assert r_get.json()["system_confidence"] == original_conf


async def test_command_book_search_stub(api_client: httpx.AsyncClient) -> None:
    r = await api_client.post(
        "/api/v1/command",
        json={"name": "BookSearch", "body": {}},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "queued"
    assert body["name"] == "BookSearch"
    assert body["started_at"] is None
    assert body["ended_at"] is None


async def test_command_unknown(api_client: httpx.AsyncClient) -> None:
    r = await api_client.post(
        "/api/v1/command",
        json={"name": "DoSomethingElse", "body": {}},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/book/search
# ---------------------------------------------------------------------------


async def test_search_books_returns_results(
    api_client: httpx.AsyncClient, mock_metadata_service: object
) -> None:
    mock_metadata_service.search_results = [  # type: ignore[attr-defined]
        _book_meta("The Martian", ol_id="OL1A", author="Andy Weir", confidence=0.8),
        _book_meta("Project Hail Mary", ol_id="OL2A", author="Andy Weir", confidence=0.7),
    ]
    r = await api_client.get("/api/v1/book/search?title=andy+weir")
    assert r.status_code == 200
    body = r.json()
    assert body["query"]["title"] == "andy weir"
    assert body["query"]["author"] is None
    assert body["total"] == 2
    assert len(body["results"]) == 2
    assert body["results"][0]["title"] == "The Martian"
    assert body["results"][1]["title"] == "Project Hail Mary"
    assert body["results"][0]["authors"][0]["name"] == "Andy Weir"


async def test_search_books_requires_title(api_client: httpx.AsyncClient) -> None:
    r = await api_client.get("/api/v1/book/search")
    assert r.status_code == 422


async def test_search_books_with_author(
    api_client: httpx.AsyncClient, mock_metadata_service: object
) -> None:
    mock_metadata_service.search_results = [  # type: ignore[attr-defined]
        _book_meta("The Martian", ol_id="OL1A", author="Andy Weir")
    ]
    r = await api_client.get("/api/v1/book/search?title=martian&author=andy+weir")
    assert r.status_code == 200
    body = r.json()
    assert body["query"]["title"] == "martian"
    assert body["query"]["author"] == "andy weir"
    assert body["total"] == 1
    assert body["results"][0]["title"] == "The Martian"


# ---------------------------------------------------------------------------
# Full happy path (sequence)
# ---------------------------------------------------------------------------


async def test_full_happy_path(api_client: httpx.AsyncClient) -> None:
    """add → list → detail → patch status → patch metadata → archive."""
    # 1. Add
    r = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    assert r.status_code == 201
    book_id = r.json()["book"]["id"]
    author_id = r.json()["book"]["authors"][0]["id"]

    # 2. List — book appears
    r = await api_client.get("/api/v1/book")
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["id"] == book_id

    # 3. Detail — authors + editions present
    r = await api_client.get(f"/api/v1/book/{book_id}")
    assert r.status_code == 200
    assert r.json()["authors"][0]["id"] == author_id

    # 4. Patch status (no confidence change)
    r = await api_client.patch(f"/api/v1/book/{book_id}", json={"status": "monitored"})
    assert r.json()["status"] == "monitored"
    assert r.json()["user_confidence"] is None

    # 5. Patch metadata (bumps confidence)
    r = await api_client.patch(f"/api/v1/book/{book_id}", json={"description": "My custom desc"})
    assert r.json()["description"] == "My custom desc"
    assert r.json()["user_confidence"] == 1.0

    # 6. Archive (soft delete)
    r = await api_client.delete(f"/api/v1/book/{book_id}")
    assert r.json()["archived"] is True

    # 7. Book still retrievable with archived status
    r = await api_client.get(f"/api/v1/book/{book_id}")
    assert r.json()["status"] == "archived"

    # 8. List?status=wanted → empty; list?status=archived → 1
    assert (await api_client.get("/api/v1/book?status=wanted")).json()["total"] == 0
    assert (await api_client.get("/api/v1/book?status=archived")).json()["total"] == 1


# ---------------------------------------------------------------------------
# Reviewer-fix regression tests
# ---------------------------------------------------------------------------


async def test_merge_external_ids_incoming_wins_on_collision(
    api_client: httpx.AsyncClient,
    mock_metadata_service: object,
    db_session: object,
) -> None:
    """Incoming external ID value wins when the same key already exists."""
    import uuid as _uuid

    from app.models.author import Author as AuthorModel

    # Add book → author created with openlibrary_author: OL999A
    r = await api_client.post("/api/v1/book", json=_title("Book One"))
    assert r.status_code == 201
    author_id = r.json()["book"]["authors"][0]["id"]

    # Manually set the same key to a stale value
    author_obj = await db_session.get(AuthorModel, _uuid.UUID(author_id))  # type: ignore[union-attr]
    author_obj.external_ids = {**author_obj.external_ids, "openlibrary_author": "OL_STALE"}
    await db_session.commit()  # type: ignore[union-attr]

    # Add second book — same mock returns ol_id=OL999A (the "incoming" fresher value)
    r2 = await api_client.post("/api/v1/book", json=_title("Book Two"))
    assert r2.status_code == 201
    assert r2.json()["book"]["authors"][0]["id"] == author_id

    # Incoming OL999A should have overwritten stale OL_STALE
    r_author = await api_client.get(f"/api/v1/author/{author_id}")
    assert r_author.json()["external_ids"]["openlibrary_author"] == "OL999A"


async def test_isbn10_x_check_digit_accepted(api_client: httpx.AsyncClient) -> None:
    """ISBN-10 ending in X is a valid Mod-11 check digit and must be accepted."""
    r = await api_client.post("/api/v1/book", json={"lookup_type": "isbn", "isbn": "080701429X"})
    assert r.status_code == 201


async def test_isbn10_invalid_last_char_rejected(api_client: httpx.AsyncClient) -> None:
    """ISBN-10 ending in a non-digit non-X character is invalid — must be 422."""
    r = await api_client.post("/api/v1/book", json={"lookup_type": "isbn", "isbn": "080701429Z"})
    assert r.status_code == 422


async def test_soft_delete_already_archived_returns_409(
    api_client: httpx.AsyncClient,
) -> None:
    """Archiving an already-archived book returns 409, not 200."""
    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    book_id = r_add.json()["book"]["id"]

    r1 = await api_client.delete(f"/api/v1/book/{book_id}")
    assert r1.status_code == 200
    assert r1.json()["archived"] is True

    r2 = await api_client.delete(f"/api/v1/book/{book_id}")
    assert r2.status_code == 409
    body = r2.json()
    assert body["error"] == "already_archived"
    assert body["details"]["book_id"] == book_id


async def test_sort_author_name_with_author_id_filter(
    api_client: httpx.AsyncClient,
    mock_metadata_service: object,
) -> None:
    """?author_id=X&sort_key=author_name must not error (Author join fixed)."""
    r = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    assert r.status_code == 201
    author_id = r.json()["book"]["authors"][0]["id"]

    r_list = await api_client.get(f"/api/v1/book?author_id={author_id}&sort_key=author_name")
    assert r_list.status_code == 200
    assert r_list.json()["total"] == 1


async def test_patch_advances_updated_at(api_client: httpx.AsyncClient) -> None:
    """PATCH must advance updated_at (Core UPDATE now sets it explicitly)."""
    import asyncio

    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    book_id = r_add.json()["book"]["id"]
    created_updated_at = r_add.json()["book"]["updated_at"]

    # Small sleep to ensure the timestamp differs
    await asyncio.sleep(0.01)

    r_patch = await api_client.patch(f"/api/v1/book/{book_id}", json={"title": "New Title"})
    assert r_patch.status_code == 200
    assert r_patch.json()["updated_at"] != created_updated_at
