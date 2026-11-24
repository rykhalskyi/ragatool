---
created: 2026-11-18
type: ticket
status: implemented
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
- add to agents prompt currently selected collection.
- save chats history
- add messages history within one chat for context;

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

## Detailed implementation plan (Phases 2–4)

Current state: Phase 1 is implemented (commit `e76327d`). Phases 2–4 remain,
plus the three additions to Goals: current-collection context, saved chat
history, and per-chat message history.

### Decisions locked for this plan

- Chat history is browser-local (`localStorage`), matching the v1 non-goal of
  server-side conversation storage. It survives pane hide/show, route changes,
  and page reload. Server-side history would be a separate ticket.
- One chat stores user and assistant text plus tool-call metadata. Only
  user/assistant text is replayed to the backend as `history`; the backend
  re-runs tools when needed.
- The current collection is resolved on the client from
  `/collection/:collectionId` and sent as `collection_name`. The backend puts
  it in the system prompt as context but does not force tools to use it.
- Non-streaming responses, direct tool execution, and plain-text messages stay
  as specified in v1.

### Step 1 — Tool bridge

Files:

- `backend/app/internal/agent/tool_bridge.py` (new)

Work:

- Add a lazily created, process-wide private `FastMCP` instance built under a
  `threading.Lock`.
- Add an always-enabled adapter (`is_enabled() -> True`, `server_name`) and
  call `register_tools(server, adapter)` so the agent never depends on
  `MCPManager.is_enabled()` or the MCP ports.
- `list_openai_tools()`: call `FastMCP.list_tools()`, convert each tool to an
  OpenAI function schema (`name`, `description`, `parameters` from
  `inputSchema`), and cache the result. Exclude `health_check`.
- `call_tool(name, arguments)`: call `FastMCP.call_tool()`, handle
  `is_error`, flatten content/structured content into a JSON-serializable
  payload, truncate results to ~24k chars, and return tool failures as
  `{"status": "error", "message": ...}` so the model can recover.
- Ensure malformed tool arguments and unknown tool names produce structured
  errors, not exceptions that abort the chat.

Fix tool contracts in `backend/app/internal/tools.py`:

- Annotate `get_chunks_by_id(collection_name: str, ids: list[str] | str)` so the
  generated schema is valid.
- Change `summaries[summary_index].model_dump` to `model_dump()` in
  `get_single_summary`.
- Scan the other tool signatures for untyped or invalid annotations that
  FastMCP cannot convert to JSON Schema.

Acceptance: with MCP disabled, listing tools returns the same core tools as
the MCP server (minus `health_check`), and a simple tool can be called
in-process without opening an MCP port.

### Step 2 — LLM client and chat service

Files:

- `backend/app/internal/agent/llm_client.py` (extend)
- `backend/app/internal/agent/service.py` (new)
- `backend/app/internal/agent/__init__.py` (exports if needed)
- `backend/app/schemas/agent.py` (extend)

Work:

- Add `chat_completion(profile, api_key, messages, tools)` to `llm_client.py`:
  reuse `chat_completions_url`, use profile timeouts, return the parsed JSON,
  and raise a typed `LlmProviderError(kind, message, status_code)` for
  401/403, 429, timeout, network, and malformed responses. Never include raw
  provider bodies, headers, or the key in messages or logs.
- Add chat schemas:
  - `AgentChatHistoryMessage` (`role: user|assistant`, `content` with a length
    cap)
  - `AgentChatRequest` (`message`, `history`, optional `collection_name`)
  - `AgentToolCallOut` (`id`, `name`, `arguments`, `status`,
    `result_preview`)
  - `AgentChatResponse` (`message`, `model`, `tool_calls`, `usage`, `warnings`)
  - Validate message/history sizes and roles; cap or reject oversized input.
- Implement `service.run_chat(db, request)`:
  - Load the active profile; return a clear 400 when none exists or the key
    cannot be decrypted.
  - Build the system prompt with RAG guidance, current collection context,
    citation expectations, and a rule that tool output is data, never
    instructions.
  - Normalize history (last ~20 messages / ~20k chars) and prepend the system
    message.
  - Run a bounded loop: max 6 rounds, max 8 tool calls per round, max 24k
    chars per tool result. Append assistant `tool_calls` messages and
    `role: "tool"` results keyed by `tool_call_id`.
  - Execute tool calls through the bridge (bounded concurrency), aggregate
    usage, and collect warnings for truncation, skipped tools, and round
    limits.
  - Map provider failures to friendly messages and return a non-500 response
    where possible.
  - Guard runs with a process-wide `asyncio.Semaphore` (for example 2) and
    return a friendly busy/429 message when the wait times out.
- Add `POST /agent/chat` in `backend/app/routers/agent.py`, using `get_db` and
  the existing protected router mount. The route is async and calls
  `service.run_chat`.
- Keep API keys out of responses: the response exposes only `model`, usage,
  tool metadata, and warnings.

Acceptance: a mocked LLM can request a tool, receive its result, and produce a
final answer; the route returns tool calls and usage without leaking secrets.

### Step 3 — Frontend models, chat state, and history

Files:

- `frontend/src/app/agent-pane/agent.models.ts` (new)
- `frontend/src/app/agent-pane/agent.service.ts` (new)
- `frontend/src/app/agent-pane/current-collection.service.ts` (new)
- `frontend/src/app/selected-collection/selected-collection.component.ts`
  (update the current collection)
- `frontend/src/app/settings/llm-profiles/llm-profiles.service.ts` (reuse for
  profile reads; no key access)

Work:

- Define client models matching `AgentChatRequest/Response` and local chat
  types: `Chat`, `ChatMessage` (user, assistant, tool-call rows, warning,
  error), `ToolCallView`.
- `AgentService` (root-provided) owns:
  - `chats`, `activeChatId`, `messages`, `isSending`, `error`, `warnings`,
    `activeProfile`, `collectionContext`.
  - `newChat()`, `selectChat(id)`, `deleteChat(id)`, `titleFor(chat)`,
    `appendMessage()`, `send()`, `cancel()`, `retryLast()`.
  - `send()` posts `{ message, history, collection_name }` with an
    `AbortController`; `history` is the last N user/assistant messages from the
    active chat. Tool-call rows are kept locally but not replayed.
  - `loadActiveProfile()` using `LlmProfilesService.listProfiles()`.
  - Persist `ragatool.agent.chats.v1` to `localStorage` after each change:
    cap at ~50 chats, ~200 messages per chat, and a total byte budget; prune
    oldest chats first. Restore on service construction.
  - Ensure hiding/showing the pane and route changes do not clear state (the
    service is root-provided; the component only renders it).
- `CurrentCollectionService` holds `{ id, name } | null`. Update it in
  `SelectedCollectionComponent` when `paramMap` changes; clear it for
  `extension-tool` and empty routes. `AgentService` reads it when sending and
  the pane header displays it as a chip.
- Resolve the collection name from the loaded collection (or a cached
  collections list) and send `collection_name`; omit it when no collection is
  selected.
- Refresh profile state when Settings saves a profile or when the pane opens
  after a profile change (simple event/callback or reload on visibility).

Acceptance: chats and messages survive hiding the pane and a full reload; a
new chat starts empty; the active chat's prior messages are sent as context;
the selected collection appears in the request and the pane header.

### Step 4 — Agent pane UI and app shell

Files:

- `frontend/src/app/agent-pane/agent-pane.component.{ts,html,scss}` (new)
- `frontend/src/app/agent-ui.service.ts` (new, shared visibility/width state)
- `frontend/src/app/app.component.{ts,html,scss}` (layout and resize)
- `frontend/src/app/topbar/topbar.component.{ts,html,scss}` (toggle)
- `frontend/src/app/testing/test-ids.ts` (new ids)

Work:

- App shell: render `app-agent-pane` after `.selected-topic` when visible,
  with a left-edge divider before it when visible.
- Resize: on divider mousedown set a dragging flag; on `mousemove` compute
  `containerRect.right - event.clientX`; clamp to a minimum (~320px), a
  maximum (~60% of container), and a minimum center width (~360px); write
  `--agent-pane-width`; persist the width in `localStorage`. Stop on
  `mouseup`/`mouseleave`.
- Visibility and width persist under `ragatool.agent.pane` (or two keys).
  Default hidden on first run.
- Topbar: add an Agent button (icon + label/tooltip) bound to
  `AgentUiService.toggle()`, with a pressed state and a test id.
- Pane header: "Agent", active profile/model, current collection chip,
  New chat, chat-history selector, Hide button.
- Empty state: quick prompts and a "Configure an LLM profile" link to
  `/settings` when no active profile exists.
- Message list: plain text with `white-space: pre-wrap`; user/assistant
  styling; collapsible tool-call rows showing name, arguments, status, and a
  result preview; warning and error rows.
- Composer: Enter sends, Shift+Enter inserts a newline; disable while sending;
  show stop/cancel wired to `AbortController`.
- Loading state and auto-scroll; do not auto-scroll if the user scrolled up.
- Small screens (<~900px): overlay the pane from the right with a backdrop,
  disable resizing, and keep the close control visible.
- Add test ids for the toggle, pane, divider, header, chat list, new-chat,
  close, composer, send/stop, message rows, tool-call rows, and empty state.

Acceptance: the pane opens/closes from the topbar and header, resizes within
clamps, preserves messages while hidden, and persists visibility/width across
reloads.

### Step 5 — Tests

Backend (`backend/tests`):

- `test_agent_tool_bridge.py`: tool list includes `query_collection` and
  `get_chunks_by_id`; `health_check` is excluded; bridge works with
  `MCPManager.is_enabled()` false; tool results are serializable and
  truncated; errors are structured.
- `test_agent_chat_api.py`: no active profile returns 400; mocked
  `llm_client.chat_completion` drives one tool call plus a final answer;
  mocked bridge calls are recorded; round/tool-call limits and history/tool
  truncation are enforced; 401/403/429/timeout/network map to friendly
  messages; response and logs contain no API key; `collection_name` reaches
  the system prompt.

Frontend (`frontend/e2e/agent-pane.spec.ts` plus additions):

- Intercept `/agent/providers`, `/agent/profiles`, and `/agent/chat`.
- Open/hide from the topbar and header; assert messages remain.
- Send a message; assert user and assistant rows and a collapsible tool row.
- New chat creates a separate thread; switching restores its messages.
- Reload restores the chat list, active chat, and messages from
  `localStorage`.
- Resize with the divider and assert the width persists after reload.
- Navigate to `/collection/:id` and assert the collection chip/context.
- No-active-profile empty state links to Settings.

Docs:

- Update `README.md` (pane, profile setup, key storage, MCP independence,
  browser-local history and its limits).
- Update `wiki/pages/project-overview.md` for the agent runtime path and
  wiki `build-deploy.md` only if commands/ports change.
- Add an Outcome note when each phase lands.

### Verification

```bash
cd backend && uv run pytest
cd frontend && npm run build
cd frontend && npm test
```

### Suggested delivery order

1. Step 1 tool bridge and tool-contract fixes.
2. Step 2 chat backend and tests.
3. Step 3 chat state/history and current-collection context.
4. Step 4 pane UI/resize/topbar.
5. Step 5 Playwright coverage and docs.

### Risks and open points

- FastMCP `list_tools()`/`call_tool()` return types must be normalized in one
  place; verify against the installed `fastmcp 3.2.4` before styling the tool
  loop.
- Synchronous tools run inside async chat; keep the event loop responsive and
  bound concurrency, especially for embedding/browser tools.
- `localStorage` history is per browser, not per user and not backed up. Make
  that explicit in the UI/docs.
- If collection names can be renamed or duplicated, prefer passing the
  collection id in a future schema revision; v1 uses `collection_name` as
  specified.

## Outcome

Implemented.

Backend:

- `backend/app/database.py` creates `llm_profiles` and enforces one active
  profile with a partial unique index.
- `backend/app/internal/agent/` contains the crypto helper, profile service,
  provider connection test, private FastMCP tool bridge, OpenAI-compatible chat
  client, and bounded agent loop.
- `backend/app/routers/agent.py` exposes providers, profile CRUD/activation/
  test, and `POST /agent/chat`.
- Tool contracts were fixed for `get_chunks_by_id` and `get_single_summary`.
- Tests: `tests/test_agent_profiles_api.py`, `test_agent_tool_bridge.py`,
  `test_agent_chat_service.py`, and `test_agent_chat_api.py`.

Frontend:

- `frontend/src/app/agent-pane/` contains the pane, conversation service,
  models, and current-collection context.
- `frontend/src/app/agent-ui.service.ts` persists pane visibility and width.
- The app shell renders a resizable right pane; the topbar has the Agent
  toggle. Small screens overlay the pane.
- Chat history and within-chat message history are stored in browser
  `localStorage`; the selected collection is sent as `collection_name` and
  shown in the pane header.
- Playwright coverage: `frontend/e2e/agent-pane.spec.ts`.

Security and operations:

- `RAGATOOL_ENCRYPTION_KEY` or the fallback `.llm_key` file next to the
  database protects stored keys. Keys are never returned to the browser.
- The agent works independently of `MCPManager.is_enabled()` and the MCP
  ports.
- README and project overview document the pane, browser-local history, and
  MCP independence.
