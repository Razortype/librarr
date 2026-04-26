# Follow-ups

Intentional technical debts and deferred work. Each item must be resolved before the feature it blocks ships.

## Security

- **Fernet encryption for IntegrationConfig** (`app/models/integration_config.py`) — `config` column is currently stored as raw bytes (plaintext stub). Implement Fernet encrypt-on-write / decrypt-on-read at the service layer before any `IntegrationConfig` write endpoint lands. Master key lives at `~/.librarr/key`.

## Schema / data integrity

- **`QualityProfile.formats` vs `QualityObject` reconciliation** — `formats` is an untyped JSON list; `QualityObject` in `app/schemas/quality.py` defines the intended shape. Wire validation through `QualityObject` at the API boundary when the quality profile endpoint is built.
- **`make_cache_key` empty-string guard** (`app/core/cache_keys.py`) — current guard uses `not source` which is falsy for empty string but passes `"0"`. Tighten to explicit `source == ""` check before the cache write layer is in use.

## Testing

- **Constraint-violation tests** — no tests verify that DB constraints fire correctly (e.g. duplicate `(book_id, author_id, role)` in `book_authors`, invalid `status` enum value). Add at least one constraint-violation test per table before integration tests run in CI.
- **Migration-running integration test** — CRUD smoke tests use `Base.metadata.create_all` and bypass Alembic. Add a test that runs `alembic upgrade head` + `alembic downgrade base` against a real Postgres (or temp container) in CI to catch migration-specific issues early.
