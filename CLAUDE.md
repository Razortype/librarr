# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project context

librarr is a self-hosted ebook/audiobook automation tool — a modern replacement for the retired Readarr. It is part of the *arr ecosystem (Sonarr, Radarr, Lidarr, Prowlarr).

This repo (`librarr`) contains the **self-hosted application** that users run on their own machines. It is open source under AGPL-3.0.

A separate private repo (`librarr-cloud`) contains the hosted metadata service. Treat the cloud as an external dependency accessed via REST API.

## Stack

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy, Alembic
- **Frontend:** Next.js (App Router), TypeScript, Tailwind, shadcn/ui
- **Database:** SQLite (default), PostgreSQL (optional)
- **Container:** Docker, docker-compose
- **Testing:** pytest, vitest

## Key conventions

(To be expanded as the architecture document grows.)

- API responses always include a `confidence` score for metadata fields
- All external API calls go through `app/integrations/` with retry + circuit breaker
- Database migrations are mandatory for schema changes (no auto-migrate in prod)
- Frontend components must be server components unless interactivity is needed

## What NOT to do

- **Do not** add audiobook, magazine, or comic support before v0.3 milestone
- **Do not** add user authentication in v0.1 (single-user assumption)
- **Do not** implement indexers — Prowlarr handles that
- **Do not** import from `librarr-cloud` directly — only via HTTP

## Roadmap reference

See ROADMAP.md for milestone scope. When in doubt, ask before expanding scope.
