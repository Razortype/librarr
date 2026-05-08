# librarr

> The book *arr that doesn't break.

Self-hosted automation for your ebook and audiobook library. Built for the post-Readarr era — with modern metadata resolution that actually works.

## Status

🚧 Early development. Not ready for use yet. [Follow the roadmap](./ROADMAP.md) or watch the repo to get notified at v0.1.

## Why librarr

Readarr was officially retired due to unfixable metadata issues. LazyLibrarian works but feels stuck in 2014. The book corner of the *arr ecosystem has been left behind while Sonarr, Radarr, and Lidarr keep evolving.

librarr aims to fill that gap with:

- **Modern metadata resolution** — LLM-assisted author disambiguation, edition matching, and series detection. The hard problem that killed Readarr is now tractable.
- **Confidence-aware results** — when metadata is uncertain, librarr tells you instead of silently picking wrong.
- **Shared metadata cache** — common books are resolved once, served to everyone. Less work for everyone's instance.
- **First-class *arr citizen** — Prowlarr, qBittorrent, SABnzbd, NZBGet, Calibre. Drop in to your existing stack.
- **Docker-first** — runs anywhere `docker compose up` works. Pi, Mini PC, NAS, VPS.

## How it works

librarr has two parts:

1. **The app** (this repo) — runs on your machine, manages your library, talks to your indexers and download clients.
2. **librarr cloud** — a hosted metadata service that helps your instance resolve book metadata. Optional but recommended. You can self-host if you prefer.

Default install uses the public cloud. Power users can BYO LLM key, run their own cloud, or skip cloud entirely (degraded metadata).

## Prerequisites

- **Python 3.13+** with [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Overmind** (local dev process manager)
  - macOS: `brew install overmind`
  - Linux: see [overmind releases](https://github.com/DarthSim/overmind/releases)
- **PostgreSQL** running natively (e.g. `brew services start postgresql@16`)
  - Default: `DATABASE_URL=postgresql+asyncpg://librarr:librarr@localhost:5432/librarr`
  - Create DB: `createdb librarr && createuser librarr`
- **Redis** running natively (e.g. `brew services start redis`)
  - Default: `REDIS_URL=redis://localhost:6379/0`

## Quick start

Coming soon. Watch the repo or check [ROADMAP.md](./ROADMAP.md) for milestones.

## Architecture

See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md). Short version: FastAPI backend, Next.js frontend, SQLite default (Postgres optional), MCP-based tool integration, CrewAI for metadata orchestration in the cloud component.

## Development

See [`docs/DEVELOPMENT.md`](./docs/DEVELOPMENT.md) for local development setup.

## Follow-ups

Open work tracked in [`web/FOLLOWUPS.md`](./web/FOLLOWUPS.md) (frontend) and [`docs/FOLLOWUPS.md`](./docs/FOLLOWUPS.md) (backend, infrastructure).

## License

[AGPL-3.0](./LICENSE). If you run librarr as a service for others, your modifications must be open-sourced under the same license.

## Inspired by

The *arr family — Sonarr, Radarr, Lidarr, Prowlarr — and the gap they left in books.
