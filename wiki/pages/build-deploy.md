---
created: 2026-11-14
type: build-deploy
summary: Build, test, run, and deploy commands for the Ragatool backend, frontend, and Docker setup.
---

# Build, Test & Deploy

## Backend

Working directory: `backend/`

```bash
uv sync                          # install dependencies
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
uv run pytest                    # full test suite
uv run pytest tests/test_url_import.py -q
```

- Python: `>=3.12`.
- No dedicated lint/format tool is configured in `backend/pyproject.toml`;
  follow `backend/.design-specs/codestyle.md`.
- `uv` manages the virtualenv and `uv.lock`.
- Runtime data: `ragatouille.db` (SQLite) and `chroma_data/` (ChromaDB).
  Override the locations with `DATABASE_PATH` and `CHROMA_PATH`. Docker
  deployments must persist these paths; the bundled compose files use
  `ragatool_data:/app/data`.
- Environment: `backend/.env` is loaded by `app/main.py` via `python-dotenv`.
  Relevant variables include `ALLOWED_ORIGINS`, `MCP_HOST`, `MCP_PORT`,
  `MCP_HTTP_HOST`, `MCP_HTTP_PORT`, and `APP_VERSION`.

## Frontend

Working directory: `frontend/`

```bash
npm install
npm start                        # ng serve
npm run build                    # production build
npm test                         # Playwright end-to-end tests
npm run test:headed
```

- Angular with standalone components and Angular Material.
- The API client under `src/app/client` is generated from the backend OpenAPI
  schema; regenerate after changing API contracts.
- Dev server typically runs on `http://localhost:4200`; the Compose frontend
  runs on port `4300` and proxies `/api` to the backend.

## Docker / Podman

From the project root:

```bash
docker compose up -d --build
docker compose -f docker-compose.ghcr.yml --env-file backend/.env up -d
```

- `docker-compose.yml` builds both images locally.
- `docker-compose.ghcr.yml` uses pre-built GHCR images.
- Backend ports: `4301` (API), `4302` (MCP SSE), `4303` (MCP HTTP).
- Frontend: `4300`.
- The backend image uses a two-stage build with `uv`; the runtime is
  `python:3.13-slim-bookworm`.
- A `fastembed_cache` volume persists downloaded embedding/reranker models.
- A `ragatool_data` volume persists `ragatouille.db` (users, sessions, tokens,
  collections) and `chroma_data` across container recreation.
- See `DOCKER_HOWTO.md` for troubleshooting.

## Quick verification

```bash
# Backend
cd backend && uv run pytest

# Frontend
cd frontend && npm run build

# Containers
docker compose ps
```
