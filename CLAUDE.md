# CLAUDE.md

Guidance for Claude Code working in this repository.

## Project context

librarr is the **self-hosted application** part of the librarr ecosystem — a modern replacement for the retired Readarr. It runs on the user's machine and orchestrates ebook/audiobook automation via the *arr stack (Prowlarr, qBittorrent, Calibre).

This repo is **public**, **AGPL-3.0**, and the public face of librarr. Anything here is visible to the world.

A separate **private** repo `librarr-cloud` contains the hosted metadata enrichment service. Treat it as an external HTTP dependency — never import from it.

A separate **private** repo `librarr-web` contains the marketing site. Not relevant to this repo.

## Stack

- **Backend:** Python 3.12+, FastAPI, async SQLAlchemy 2.0, Alembic, Pydantic v2
- **Frontend:** Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui
- **Database:** SQLite default, PostgreSQL optional
- **Async tasks:** Arq (Redis-backed)
- **Container:** Docker, docker-compose
- **Testing:** pytest + httpx for backend, vitest + Testing Library for frontend
- **Linting:** ruff (Python), prettier + eslint (TS)
- **Package mgmt:** uv for Python, pnpm for Node

## Architecture overview

Three-layer architecture:

1. **Web UI (Next.js)** → REST calls to backend
2. **Backend (FastAPI)** → orchestrates everything: DB, *arr integrations, librarr-cloud
3. **External integrations** → Prowlarr (search), qBittorrent (download), Calibre (library), librarr-cloud (metadata)

Backend talks to librarr-cloud over HTTPS for metadata enrichment. Cloud is **graceful-degradation optional**: if cloud is down, app falls back to direct Open Library calls with reduced confidence scores.

## Database schema (core entities)

All IDs are **UUID v7** (timestamp-ordered).

- **Author** — canonical_name, sort_name, aliases (jsonb), birth/death year, external_ids, biography, image_url, system_confidence, user_confidence, effective_confidence (computed)
- **Book** — title, original_title, original_language (ISO 639-1), publication_year, description, series_id (nullable FK), series_position (float), external_ids, status (`wanted`/`monitored`/`unmonitored`/`archived`), confidence triple
- **book_authors** (M2M) — book_id, author_id, role (`primary`/`co_author`/`contributor`/`translator`/`illustrator`), position (int)
- **Edition** — book_id, isbn_10, isbn_13, asin, format (`hardcover`/`paperback`/`ebook`/`audiobook`/`large_print`/`mass_market`), language, publisher, publication_date, page_count, audio_duration_seconds, narrators (jsonb), translators (jsonb), cover_url, external_ids, confidence triple
- **Series** — name, description, external_ids, confidence triple

**Confidence triple pattern:** every metadata entity has `system_confidence` (cloud-computed), `user_confidence` (null unless manually edited), `effective_confidence` (`COALESCE(user_confidence, system_confidence)`). Always read effective in UI; write to user when user edits.

Auxiliary tables: `Download`, `QualityProfile`, `Setting` (key-value), `IntegrationConfig` (Fernet-encrypted secrets), `MetadataCache` (local cache of cloud responses), `ActivityLog` (event log, write-only in MVP).

See `docs/ARCHITECTURE.md` for full schema details.

## Cloud API contract (how this app talks to librarr-cloud)

Base URL configurable via `LIBRARR_CLOUD_URL` env, default `https://api.librarr.com/v1`.

Auth: `X-Librarr-Key` header. MVP uses a hardcoded shared key shipped with the app — proper accounts come in v0.2.

Endpoints used:

- `POST /v1/metadata/enrich` — request enrichment for a query
- `GET /v1/metadata/enrich/{request_id}` — poll for async result
- `GET /v1/metadata/lookup` — cache-only lookup by ISBN/external_id
- `POST /v1/metadata/feedback` — report user corrections (fire-and-forget)
- `GET /v1/version` — check minimum supported app version

**Async pattern: polling.** Self-hosted users typically have no public IP — webhooks won't work. Poll every 2-3s, exponential backoff up to 30s.

**Graceful degradation:** if cloud responds slowly or 5xx, fall back to direct Open Library calls within 5s timeout. Mark resulting metadata with `system_confidence ≤ 0.6`.

**Rate limit handling:** if 429, respect `Retry-After` header. Don't retry within budget.

## Conventions

### Python

- Type hints on every function. Use `from __future__ import annotations`.
- Pydantic v2 models for everything crossing a boundary (API request/response, DB write payloads, cloud calls).
- SQLAlchemy 2.0 async style only. No legacy `Query` API.
- Alembic for every schema change. **Never** `Base.metadata.create_all()` in production code path.
- All external HTTP calls go through `app/integrations/<service>/client.py` with **tenacity** retry (3 attempts, exponential, jitter) and circuit breaker.
- `httpx.AsyncClient` for HTTP. Never `requests`.
- Errors are explicit. No bare `except`. Custom exception classes in `app/core/exceptions.py`.
- Logging via `structlog` JSON-formatted. Include `trace_id` in every log line.

### File layout

```
app/
├── api/               # FastAPI routers, /api/v1/*
├── core/              # Config, exceptions, security, db engine
├── models/            # SQLAlchemy ORM models
├── schemas/           # Pydantic models (API contracts)
├── integrations/      # External service clients
│   ├── prowlarr/
│   ├── qbittorrent/
│   ├── calibre/
│   └── librarr_cloud/
├── services/          # Business logic, called by API routes
├── tasks/             # Arq async task definitions
└── main.py            # FastAPI app factory

tests/
├── unit/
├── integration/
└── conftest.py

web/
└── (Next.js standard layout)
```

### API design

Mirror *arr conventions where sensible:
- `/api/v1/system/status` — health
- `/api/v1/book` — CRUD on books
- `/api/v1/author` — CRUD on authors
- `/api/v1/queue` — current downloads
- `/api/v1/wanted/missing` — books wanted but not yet downloaded
- `/api/v1/quality/profile` — quality profile management
- `/api/v1/command` — async commands (refresh, scan, etc.)

This makes librarr feel native to users coming from Sonarr/Radarr.

### Frontend

- Server components by default. `"use client"` only when interactivity needed.
- Tailwind only — no CSS modules, no styled-components.
- shadcn/ui for primitives. Don't reinvent buttons/dialogs.
- Server actions for mutations, not REST POST from client where possible.
- Confidence scores **must be visible** in UI when below 0.85. Color-code: green ≥0.85, amber 0.7-0.84, red <0.7.

### Commits

Conventional Commits format:
- `feat:` new feature
- `fix:` bug fix
- `refactor:` no behavior change
- `test:` test only
- `docs:` docs only
- `chore:` maintenance

One logical change per commit. Don't combine refactor and feature.

### Security

- **Never** log secrets, API keys, passwords. Sanitize before logging.
- All `IntegrationConfig.config` secrets encrypted at rest via Fernet. Master key at `~/.librarr/key`, generated on first run, user backs up.
- All user input parameterized via SQLAlchemy. **No** raw SQL with string interpolation.
- CORS locked down by default. User configures allowed origins.

## Commit conventions

- **No `Co-Authored-By: Claude` trailers.** Author is the user only. AI assistance is acknowledged in README; commits stay clean.
- **No `git -C <path>` flags.** Run git from the working directory.
- **Propose before committing.** Before executing any commit, surface the proposed message in chat and wait for explicit user approval. This applies to delegated subagent commits too — subagents stage files, surface the message, the user approves, then commit.

## What NOT to do

- **Do not** import from `librarr-cloud`. Cloud is an external HTTP service.
- **Do not** implement indexers. Prowlarr handles that.
- **Do not** add auth/multi-user support in v0.1 (single-user assumption).
- **Do not** add audiobook, magazine, or comic features before v0.3 milestone.
- **Do not** use blocking I/O in async paths. Always `await`.
- **Do not** auto-create DB tables in production code. Migrations only.
- **Do not** scrape Goodreads. TOS violation, fragile, legal grey.
- **Do not** ship features not in `ROADMAP.md` for current milestone.

## Subagents available

- `implementer` — writes code to a defined contract
- `reviewer` — fresh-context code review on diffs
- `arr-specialist` — *arr ecosystem domain knowledge (Prowlarr, qBit, Calibre, etc.)
- `librarian` — book metadata, schema design, migration writing

Delegate based on task scope. See `.claude/agents/*.md` for each agent's role.

## Roadmap reference

See `ROADMAP.md` for milestone scope. When unsure if work fits current milestone, ask before expanding.
