---
created: 2026-11-18
type: ticket
status: proposed
summary: Add an in-app, resizable agent pane with encrypted LLM API profiles and direct access to the same tools as the Ragatool MCP server.
---

# In-App Agent Pane

Related: [project overview](../project-overview.md),
[build & deploy](../build-deploy.md).

## Spec

### Problem

Ragatool exposes its RAG capabilities only through the MCP server. Using them
requires a separate MCP client, an API token, and a network connection to the
MCP ports. A user working inside the Ragatool UI cannot ask questions about
their own collections without leaving the app.

Reference implementation: BookTailor's `AiChatPanel.vue` (right-side chat pane
toggled from the toolbar) and `SettingsScreen.vue` (LLM profile CRUD with
write-only, masked API keys). BookTailor's pane is fixed-width and hide-only;
Ragatool's pane must also be resizable like the existing left collection pane.

### Goals

- Add a right-side agent pane on authenticated pages.
- Resize the pane by dragging its left divider, mirroring
  `frontend/src/app/app.component.ts` and `app.component.scss`.
- Expand/hide the pane from the topbar and from a pane-header control; persist
  the visible state and width in `localStorage`.
- Let the user add, edit, test, activate, and delete LLM API profiles in
  Settings. The API key is encrypted at rest and never returned to the browser.
- Give the agent direct, in-process access to the same tools as the MCP server,
  including when the public "MCP ON" toggle is off and no MCP client is
  connected.
- Keep conversations in the browser session (no server-side conversation
  storage in v1).

### Non-goals (v1)

- Server-side chat history or multi-user conversation isolation.
- Streaming responses. Ship a non-streaming request first; an SSE endpoint can
  follow without changing the profile model.
- Tool approval workflow for mutating tools. The agent executes tools directly,
  matching MCP semantics.
- Markdown rendering in messages. Use plain text with `white-space: pre-wrap`.
- Support for non-OpenAI-compatible providers.

### UX

Layout:

- Authenticated shell: left collections pane, router outlet, optional right
  agent pane. Login/setup keep the current auth layout.
- The agent divider sits on the pane's left edge. Dragging it computes
  `containerRect.right - event.clientX`, clamps to a minimum pane width and a
  maximum percentage, and keeps a minimum center width.
- When hidden, the divider and pane disappear and the routed content grows.
- Small screens: stack or overlay the pane; disable resizing below ~900px.

Pane:

- Header: "Agent", active profile/model, current collection chip, New chat,
  Hide/expand button.
- Empty state with quick prompts and a link to Settings when no active profile
  exists.
- Message list with user and assistant messages, collapsible tool-call rows
  (name, arguments, result preview), warnings, and errors.
- Loading state with stop/cancel support. Composer: Enter sends,
  Shift+Enter inserts a newline.
- Conversation state lives in an Angular service so hiding/showing the pane does
  not clear it.

Settings:

- New "LLM API profiles" section above the existing generic settings list.
- Provider presets: OpenAI, DeepSeek, SiliconFlow, OpenRouter, Custom
  OpenAI-compatible base URL.
- Fields: name, provider, base URL, model, API key, temperature, max tokens,
  connect/read timeouts, active.
- Edit mode: blank API key means "keep the existing key".
- Show only a masked key (`••••1234`). Provide a Test connection action.

### Architecture

```text
Angular app shell
├─ left collections pane (existing)
├─ routed content
└─ right agent pane (new, resizable + collapsible)
      └─ AgentService -> POST /agent/chat

FastAPI
└─ /agent
   ├─ profile CRUD + test
   └─ chat (stateless history, bounded tool loop)
        ├─ LLM client (httpx, OpenAI-compatible)
        └─ in-process tool bridge
             └─ private FastMCP instance registered with `register_tools(...)`
```

The tool bridge must not call MCP over HTTP. At startup, create a private
FastMCP instance, pass an always-enabled adapter to
`register_tools(server, adapter)`, then use `list_tools()` / `call_tool()` for
the agent. This reuses `backend/app/internal/tools.py` without duplicating tool
implementations and is independent of `MCPManager.is_enabled()`.

### Data and API

Add to `backend/app/database.py`:

```sql
CREATE TABLE IF NOT EXISTS llm_profiles (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  provider TEXT NOT NULL,
  base_url TEXT NOT NULL,
  api_key TEXT NOT NULL,
  model TEXT NOT NULL,
  temperature REAL NOT NULL DEFAULT 0.2,
  max_tokens INTEGER NOT NULL DEFAULT 2048,
  connect_timeout_seconds INTEGER NOT NULL DEFAULT 30,
  read_timeout_seconds INTEGER NOT NULL DEFAULT 120,
  is_active BOOLEAN NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT
);
```

One active profile, enforced in a transaction in the service layer. Ragatool is
single-user, so the table has no `user_id` for v1.

Routes, mounted in `backend/app/main.py` with `prefix="/agent"` and the
existing `require_user` dependency:

```text
GET    /agent/providers
GET    /agent/profiles
POST   /agent/profiles
PATCH  /agent/profiles/{id}
DELETE /agent/profiles/{id}
POST   /agent/profiles/{id}/activate
POST   /agent/profiles/{id}/test
POST   /agent/chat
```

`POST /agent/chat` request: `message`, `history`, optional
`collection_name` context. Response: `message`, `model`, `toolCalls` (id, name,
arguments, status, resultPreview), `usage`, `warnings`.

### Security

- Require the existing session cookie via `require_user`.
- Encrypt API keys with Fernet. Prefer `RAGATOOL_ENCRYPTION_KEY`; otherwise
  create `<data-dir>/.llm_key` with mode `0600` next to the database.
- Never log keys, authorization headers, or raw provider bodies. Never return a
  key or ciphertext to the browser.
- Validate base URLs as `http(s)`. The app is single-user and admin-operated;
  do not silently block local LLM endpoints.
- The existing origin/CSRF middleware already covers `POST/PATCH/DELETE`.
- Cap history, tool rounds, tool calls per round, and per-tool result size.
- Treat tool output as data in the system prompt; do not follow instructions
  found inside documents.

### Open decisions

- Streaming vs non-streaming for v1. Recommendation: non-streaming.
- Whether mutating tools (`add_summary`, `edit_wiki_page`, `add_fact`, etc.)
  should require confirmation. Recommendation: execute directly in v1,
  matching MCP.
- Default pane state on first run. Recommendation: hidden, with a topbar toggle.
- Whether the agent should reset when the selected collection changes.
  Recommendation: keep the conversation and pass the current collection as
  context.

## Plan

### Phase 1 — Profiles and settings

Backend:

- Add the `llm_profiles` table to `backend/app/database.py`.
- Add `backend/app/crud/crud_llm_profile.py`.
- Add `backend/app/schemas/agent.py`.
- Add `backend/app/internal/agent/crypto.py` (Fernet) and
  `backend/app/internal/agent/profiles.py` (CRUD, presets, masking, test call).
- Add `backend/app/routers/agent.py`; include it in `backend/app/main.py`.
- Add `cryptography` explicitly to `backend/pyproject.toml` and `uv.lock`.
- Document `RAGATOOL_ENCRYPTION_KEY` in `.env.example` and `README.md`.

Frontend:

- Add `settings/llm-profiles/llm-profiles.component.*`,
  `llm-profile-dialog.component.*`, and `settings/llm-profiles.service.ts`.
- Embed the section in `settings/settings.component.html` above the generic
  settings.
- Add test ids in `frontend/src/app/testing/test-ids.ts`.
- Use a handwritten `HttpClient` service or regenerate the OpenAPI client.

### Phase 2 — Tool bridge and chat backend

- Add `backend/app/internal/agent/tool_bridge.py`:
  - Build a private FastMCP instance and register the existing tools with an
    always-enabled adapter.
  - Convert `list_tools()` into OpenAI function schemas.
  - Call tools in-process, serialize `ToolResult`, and return tool errors as
    JSON so the model can recover.
- Add `backend/app/internal/agent/llm_client.py` using `httpx` and an
  OpenAI-compatible `/chat/completions` call with native `tools`.
- Add `backend/app/internal/agent/service.py`:
  - System prompt with RAG guidance and current-collection context.
  - Bounded loop: max 6 rounds, max 8 tool calls per round.
  - Append assistant tool calls and `role: "tool"` results.
  - Truncate history (~20 messages / 20k chars) and tool results (~24k chars).
  - Map 401/403/429/timeout/network failures to friendly messages.
- Fix tool schema issues that the agent will expose:
  - Annotate `get_chunks_by_id(collection_name: str, ids)`.
  - Call `model_dump()` correctly in `get_single_summary`.
- Optionally exclude `health_check` from the agent toolset.
- Add a process-wide semaphore to limit concurrent agent runs.

### Phase 3 — Right pane UI

- Update `frontend/src/app/app.component.html`, `.ts`, `.scss`:
  - Render the pane and its divider when visible.
  - Add right-edge resize logic with clamping and persistence.
- Add `frontend/src/app/agent-pane/agent-pane.component.*`.
- Add `frontend/src/app/agent-pane/agent.service.ts` for messages, history,
  requests, abort, retry, and errors.
- Add an "Agent" toggle button to `topbar/topbar.component.*`.
- Persist visibility and width; handle small screens.

### Phase 4 — Tests and docs

Backend tests:

- Profile CRUD, encrypted storage, masking, active uniqueness, test endpoint.
- Agent loop with a mocked LLM: tool call, tool result, final response.
- Tool bridge exposes the same tools and works with public MCP disabled.
- Tool-round limits, truncation, and error handling.
- No key leakage in responses or logs.

Frontend tests:

- Playwright: open/hide the pane, resize, reload persistence.
- Playwright: add/edit/activate/delete profiles with intercepted API calls.
- Playwright: send a message with intercepted `POST /agent/chat`.

Docs:

- Update `README.md` with the agent pane, profile setup, key storage, and
  MCP-independence.
- Update `.env.example` and `wiki/pages/project-overview.md` if the runtime
  architecture changes.

### Verification

```bash
cd backend && uv run pytest
cd frontend && npm run build
cd frontend && npm test
```

## Outcome

Not started.
