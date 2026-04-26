# Follow-ups

Intentional technical debts and deferred work. Each item must be resolved before the feature it blocks ships.

## Security

- **Fernet encryption for IntegrationConfig** (`app/models/integration_config.py`) — `config` column is currently stored as raw bytes (plaintext stub). Implement Fernet encrypt-on-write / decrypt-on-read at the service layer before any `IntegrationConfig` write endpoint lands. Master key lives at `~/.librarr/key`.

## Schema / data integrity

- **`QualityProfile.formats` vs `QualityObject` reconciliation** — `formats` is an untyped JSON list; `QualityObject` in `app/schemas/quality.py` defines the intended shape. Wire validation through `QualityObject` at the API boundary when the quality profile endpoint is built.
- **`make_cache_key` empty-string guard** (`app/core/cache_keys.py`) — current guard uses `not source` which is falsy for empty string but passes `"0"`. Tighten to explicit `source == ""` check before the cache write layer is in use.

## Infrastructure / performance

- **Circuit breaker (aiobreaker)** — tenacity-only is sufficient for A. Introduce a real circuit breaker when concurrent metadata enrichment lands (multiple simultaneous search requests) — at that scale, repeated failures against OL/cloud cascade. Add before the concurrent enrichment Arq task ships.
- **Move cloud polling to Arq task** — the metadata service currently drives the cloud poll loop synchronously. This blocks a worker for up to 30s under slow cloud responses. Move to an Arq background task before concurrent search is exposed via API endpoints.
- **OL startup health check** — ping `GET /api/` on OL client startup (via FastAPI lifespan), log result, continue regardless. Gives early visibility into OL availability without blocking startup.

## Code quality / OL client

- **Extract `@retry` decorator to module-level constant** (`app/integrations/openlibrary/client.py`) — the same `@retry(...)` config is copy-pasted on all four public methods. Extract to `_OL_RETRY = retry(...)` and apply `@_OL_RETRY` to eliminate duplication.
- **OL `fields=*` on search requests** — every `search_books` call requests all available OL fields. A targeted field list (only fields actually used in `_normalize_search_doc`) would reduce response payload on large result sets. Low priority until OL response sizes become measurable.
- **`load_fixture` as a bare function** (`tests/conftest.py`) — works as a utility, but as a bare function (not a `pytest.fixture`) it can't be parameterized later. Consider converting to a fixture when parameterized fixture tests are needed.
- **`TimeoutError` catch comment** (`app/services/metadata.py`) — catching bare `TimeoutError` is correct for Python 3.13+ (it's a superclass of `asyncio.TimeoutError` since 3.11). Add an inline comment so future readers don't "fix" it to `asyncio.TimeoutError` if the Python floor ever drops.

## Testing

- **Constraint-violation tests** — no tests verify that DB constraints fire correctly (e.g. duplicate `(book_id, author_id, role)` in `book_authors`, invalid `status` enum value). Add at least one constraint-violation test per table before integration tests run in CI.
- **Migration-running integration test** — CRUD smoke tests use `Base.metadata.create_all` and bypass Alembic. Add a test that runs `alembic upgrade head` + `alembic downgrade base` against a real Postgres (or temp container) in CI to catch migration-specific issues early.
