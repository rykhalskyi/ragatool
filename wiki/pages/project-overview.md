---
created: 2026-11-14
type: overview
summary: Tech stack, architecture, folder structure, and key concepts for Ragatool.
---

# Project Overview

Ragatool is a locally deployable RAG and MCP server. It vectorizes books,
specifications, documentation, code, and web pages into configurable
"collections", then exposes retrieval to AI agents through a unified MCP
server. Third-party integrations (OnlyOffice, Thunderbird, Outlook) connect
over WebSocket through an extension protocol.

## Tech stack

- **Backend:** Python 3.12+, FastAPI, Uvicorn, Pydantic, SQLAlchemy.
- **Vector store:** ChromaDB (persistent, `backend/chroma_data`).
- **Metadata store:** SQLite (`backend/ragatouille.db`).
- **Embeddings:** FastEmbed via `app/internal/embedding_manager.py`.
- **MCP:** FastMCP with SSE and HTTP transports (`app/internal/mcp_manager.py`).
- **Ingestion:** trafilatura / BeautifulSoup (URL), PyPDF, Docx2txt,
  LangChain text splitters.
- **Frontend:** Angular (standalone components, Angular Material), generated
  OpenAPI client under `frontend/src/app/client`.
- **Packaging:** Docker / Docker Compose, `uv` for backend dependencies.

## Architecture

```
Angular UI ──HTTP──> FastAPI routers ──> CRUD / models / internal managers
                            │
                            ├── SQLite (metadata, logs, tasks, settings, files)
                            ├── ChromaDB (chunks + embeddings)
                            ├── BackgroundTaskDispatcher (worker threads)
                            ├── MessageHub (SSE updates to the UI)
                            └── MCPManager (FastMCP SSE + HTTP)
```

- **Routers** (`app/routers`) expose REST endpoints.
- **CRUD** (`app/crud`) handles SQLite and Chroma access.
- **Models** (`app/models`) hold import and business logic.
- **Internal** (`app/internal`) holds singletons and core logic: embedding,
  vector store, retrieval/reranking, chunking, crawler, task dispatcher,
  message hub, MCP, and extensions.
- **Schemas** (`app/schemas`) define API and validation contracts.

## Folder structure

```
backend/
├── app/
│   ├── crud/          # SQLite + Chroma data access
│   ├── internal/      # managers, embedding, retrieval, crawler, MCP
│   ├── models/        # import logic (file, URL)
│   ├── routers/       # FastAPI endpoints
│   ├── schemas/       # Pydantic contracts
│   ├── database.py    # schema + seed settings
│   ├── dependencies.py
│   └── main.py
├── tests/             # pytest suite
├── scripts/           # retrieval evaluation helpers
└── pyproject.toml
frontend/
├── src/app/           # Angular components, services, generated client
├── e2e/               # Playwright tests
└── package.json
plugins/               # OnlyOffice, Thunderbird, Outlook integrations
```

## Key concepts

- **Collection:** the core unit of organization; owns an embedding model,
  chunking settings, and a Chroma collection.
- **Import:** a pipeline that extracts text, chunks it, embeds it, and stores
  it in a collection. File and URL imports are implemented in `app/models`.
- **Two-step import:** optionally stage parsed content as temp files for
  preview before embedding.
- **Chunk:** a text segment with offsets stored as Chroma metadata
  (`source`, `chunk`, `ts`, `char_start`, `char_end`).
- **Summary hierarchy:** CHUNKS / CHAPTER / BOOK summaries plus wiki pages
  managed through the RAG wiki skills.
- **LLM profiles:** OpenAI-compatible provider profiles with Fernet-encrypted
  API keys, used by Ragatool's built-in agent.
- **Extensions:** WebSocket-connected plugins exposed as MCP tools.
- **MessageHub:** broadcasts progress, info, and log messages to the UI via
  SSE; also persists log messages.

## Runtime ports

| Service | Port |
|---|---|
| FastAPI backend | 8000 (Compose: 4301) |
| MCP SSE | 8001 (Compose: 4302) |
| MCP HTTP | 8002 (Compose: 4303) |
| Angular frontend (Compose) | 4300 |
