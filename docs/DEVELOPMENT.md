# Local development

This guide assumes macOS. Linux paths are similar; Windows users will likely want WSL.

## Prerequisites

- Python 3.13 (managed via `uv`)
- Node.js 20+ and `pnpm`
- PostgreSQL 16 (`brew install postgresql@16 && brew services start postgresql@16`)
- [Overmind](https://github.com/DarthSim/overmind) for process management (`brew install overmind`)

## First-time setup

```bash
# Install Python and JS dependencies
uv sync
cd web && pnpm install && cd ..

# Configure environment
cp .env.example .env
# The defaults assume Postgres on localhost. Edit DATABASE_URL if your setup differs.

# Create the database role and schema
psql postgres -c "CREATE ROLE librarr WITH LOGIN PASSWORD 'librarr';"
psql postgres -c "CREATE DATABASE librarr OWNER librarr;"

# Run migrations
uv run alembic upgrade head
```

## Running the stack

Backend and frontend together via Overmind (reads `Procfile`):

```bash
make dev
```

Or run them separately in two terminals:

```bash
# Terminal 1 — backend
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd web && pnpm dev
```

Backend at http://localhost:8000, frontend at http://localhost:3000.

## Frontend mock toggle

By default the frontend reads from a mock data layer (`web/src/lib/use-mock.ts`) so pages render without a backend. To wire real API calls, edit `web/.env.local`:

```
NEXT_PUBLIC_USE_MOCK=false
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Restart the frontend dev server after changing `.env.local`.

## Migrations

Create a new migration:
```bash
uv run alembic revision --autogenerate -m "describe the change"
```

Apply migrations:
```bash
uv run alembic upgrade head
```

Roll back one revision:
```bash
uv run alembic downgrade -1
```

## Tests

```bash
make test           # all unit + integration tests
make test-network   # tests that hit external services (slow)
make lint           # ruff check
make format         # ruff format
```
