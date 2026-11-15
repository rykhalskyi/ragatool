---
created: 2026-11-15
type: ticket
status: proposed
summary: Add single-user login, first-run setup, and revocable API tokens for the UI, MCP servers, and extension WebSockets.
---

# Secure Ragatool — Single-User Auth and API Tokens

Source plan: [01-secure-ragatool.md](../../raw/01-secure-ragatool.md).
Related: [project overview](../project-overview.md),
[build & deploy](../build-deploy.md).

## Spec

### Problem

Ragatool currently has no authentication. Every REST endpoint, both MCP
transports, and the extension WebSocket are reachable anonymously. The app is
usually deployed on a local network with ports `4301`/`4302`/`4303` exposed.

Relevant files:

- `backend/app/main.py:74` includes all routers with no auth dependency.
- `backend/app/internal/mcp_manager.py:46` creates FastMCP servers with no
  `auth=`.
- `backend/app/internal/tools.py` exposes query and write tools.
- `backend/app/routers/extensions.py:41` accepts extension WebSockets.
- `backend/app/schemas/user.py` exists but is empty.
- `frontend/src/app/client/core/OpenAPI.ts` already supports credentials.
- `frontend/src/app/settings` holds the existing settings UI.

### Goals

- Require login for all UI/API access; remove anonymous access.
- Provide a first-run setup flow without Google/OAuth or external providers.
- Require a bearer token for every MCP connection, with immediate revocation.
- Protect extension WebSockets with the same tokens.
- Add a dedicated Access page to create and revoke tokens.
- Keep deployment offline and self-contained.

### Non-goals

- Multi-user accounts, roles, or per-collection permissions.
- OAuth/OIDC, social login, passkeys, or email recovery.
- Token scopes; Phase 1 tokens grant full access.
- Changes to the RAG, import, or summary pipelines.

### Decisions

| Decision | Choice |
|---|---|
| UI authentication | Username + password, signed `HttpOnly` session cookie |
| First-run bootstrap | `/setup` page gated by a one-time code printed in backend logs |
| Machine authentication | Opaque `ragt_...` bearer tokens hashed in SQLite |
| Token management | Dedicated `/access` page with create/revoke |
| Extension WebSockets | Same bearer tokens as MCP |

Recorded as decisions `D-02` and `D-03` in [decisions.md](../../decisions.md).

### Architecture

```
Angular UI ──cookie──> FastAPI REST ──> session check ──> routers
                            │
                            └── SQLite: auth_users, api_tokens

MCP client ──Bearer ragt_...──> FastMCP SSE/HTTP ──> DbTokenVerifier
                            │
                            └── SQLite: api_tokens (hash lookup)

Plugin ──Bearer / ?token=──> /extensions/ws ──> token check
```

### Data model

```sql
CREATE TABLE IF NOT EXISTS auth_users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    session_version INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_tokens (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    prefix TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME,
    revoked_at DATETIME
);
```

- Password hashes use bcrypt (add `bcrypt` explicitly to `pyproject.toml`).
- Tokens are `ragt_` + `secrets.token_urlsafe(32)`; only the SHA-256 hex digest
  is stored. `prefix` is the first 8 characters for display.
- `session_version` is embedded in the session cookie; incrementing it
  invalidates all existing sessions.

### API contract

Public:

- `GET /auth/status` -> `{ initialized: bool }`
- `POST /auth/setup` -> `{ username, password, setup_code }`
- `POST /auth/login` -> `{ username, password }`
- `GET /version`

Session-protected:

- `POST /auth/logout`
- `GET /auth/me` -> `{ id, username }`
- `GET /tokens` -> list of `{ id, name, prefix, created_at, last_used_at, revoked_at }`
- `POST /tokens` -> `{ name }`; response includes plaintext `token` once
- `DELETE /tokens/{id}` -> `204`

### First-run flow

1. Startup sees `auth_users` empty and no env hash. Generate
   `secrets.token_urlsafe(16)` and print it once to stdout:
   `RAGATOOL SETUP CODE: <code>`.
2. `GET /auth/status` returns `initialized: false`; the UI redirects to
   `/setup`.
3. Setup asks for username (pre-filled `admin`), password, confirmation, and
   the setup code.
4. `POST /auth/setup` verifies the code with `secrets.compare_digest`, checks
   in a transaction that the table is still empty, creates the user, opens a
   session, and invalidates the in-memory code.
5. `/setup` becomes disabled; later visits redirect to `/login`.
6. Each restart before setup prints a fresh code. The code is never persisted
   to the `logs` table.

### Environment

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Session cookie signing; ephemeral with a warning if unset |
| `COOKIE_SECURE` | `true` behind TLS, default `false` for local HTTP |
| `SESSION_MAX_AGE_HOURS` | Session lifetime, default `168` |
| `RAGATOOL_ADMIN_USERNAME` | Optional headless seed, default `admin` |
| `RAGATOOL_ADMIN_PASSWORD_HASH` | Optional headless seed; skips `/setup` |

If a user already exists, env seeding is ignored.

## Plan

### 1. Auth core (`backend/app/internal/auth.py`)

- `hash_password`, `verify_password`, `generate_token`, `hash_token`.
- Session helpers over Starlette `SessionMiddleware`; add `itsdangerous` as an
  explicit dependency.
- `require_user` FastAPI dependency; `require_setup_available`.
- Origin check for state-changing requests; `SameSite=Lax` cookies.
- CLI entry points:
  - `python -m app.internal.auth hash-password`
  - `python -m app.internal.auth reset-password` (increments
    `session_version`)

### 2. Persistence

- Add tables to `create_tables` in `backend/app/database.py`.
- New `backend/app/crud/crud_user.py` and `crud_token.py`:
  - create/find user, verify credentials, reset password.
  - create/list/find-by-hash/revoke/touch tokens.
- All list responses exclude `password_hash` and `token_hash`.

### 3. REST routes

- New `backend/app/routers/auth.py`.
- New `backend/app/routers/tokens.py`.
- Wire in `backend/app/main.py`; add `Depends(require_user)` to every data
  router. Keep only the public list above unauthenticated.
- Return `401` with `WWW-Authenticate` semantics for missing/expired sessions.

### 4. MCP authentication

- Implement `DbTokenVerifier(TokenVerifier)` in `app/internal/auth.py`:
  - `async verify_token(token)` hashes, looks up an active row, touches
    `last_used_at`, returns `AccessToken(...)`; returns `None` otherwise.
- Pass `auth=DbTokenVerifier()` to both FastMCP instances in
  `MCPManager.enable()`.
- Verify early that both SSE and HTTP transports reject missing/invalid tokens
  and accept a valid one.

### 5. Extension WebSocket

- In `backend/app/routers/extensions.py`, extract the token from
  `Authorization: Bearer` or `?token=` and validate before `accept()`.
- Close with code `1008` on failure.
- Update the OnlyOffice, Thunderbird, and Outlook plugins to send a configured
  token. Browser WebSocket clients use `?token=`; C# uses the header.

### 6. Frontend

- Set `OpenAPI.WITH_CREDENTIALS = true` in `app.component.ts`.
- New `AuthService` and guard:
  - `/auth/status` decides `/setup` vs `/login` vs app.
  - Any `401` redirects to `/login`.
- `SetupComponent`: username, password, confirm, setup code.
- `LoginComponent`: username + password.
- `AccessTokensComponent` at `/access`:
  - table: name, prefix, created, last used, revoked
  - create dialog, copy-once dialog, revoke confirmation
  - optional "Change password" section
- Add the Access route in `app.routes.ts` and a nav button in
  `topbar.component.html`.
- Regenerate the OpenAPI client after backend contracts land.

### 7. Docs and deployment

- Update `backend/.env` documentation and `docker-compose*.yml` env passthrough.
- Update README MCP examples:

```json
"Ragatool": {
  "url": "http://localhost:4303/mcp",
  "headers": { "Authorization": "Bearer ragt_..." }
}
```

- Document plugin token setup and the difference between header and
  `?token=` transports.

### 8. Tests

Backend (`uv run pytest`):

- First-run status, wrong setup code, successful setup, second setup rejected.
- Login/logout, wrong password, protected route returns `401`.
- Token create/list/revoke; hashes and plaintext never returned by list.
- `DbTokenVerifier` accepts, rejects revoked, updates `last_used_at`.
- Extension WebSocket rejects missing/invalid and accepts valid tokens.
- Env password-hash seeding skips `/setup`; existing user ignores env changes.

Frontend:

- Playwright: setup -> login -> create token -> revoke token -> logout.

### 9. Acceptance

- Fresh database shows a setup code in logs and `/setup` works only with it.
- No anonymous REST, MCP, or WebSocket access.
- A token created in `/access` works against both MCP ports and the extension
  WebSocket; revoking it takes effect immediately.
- Logout and password reset invalidate existing sessions.
- Existing databases upgrade via `CREATE TABLE IF NOT EXISTS` without manual
  migration.

### 10. Risks

- Some MCP clients may attempt OAuth discovery instead of sending a static
  header; fallback is a minimal local token issuer.
- Browser WebSocket cannot set headers, so plugins must use `?token=` and URLs
  may appear in proxy logs.
- `COOKIE_SECURE=false` is required for plain-HTTP LAN use; document the
  trade-off.
- The one-time setup code is printed to container logs; treat logs as sensitive
  until setup completes.

## Outcome

Not implemented yet.
