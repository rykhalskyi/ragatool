# Decisions

Append-only decision record. The "why" lives here; the full change history lives in git.

- [2026-11-14] D-01 — Use bundled Playwright Chromium with auto-escalation and a full URL crawler overhaul — because CSR pages need rendering and self-contained deployment avoids external rendering APIs.
- [2026-11-15] D-02 — Use local username/password with signed session cookies for the UI and hashed opaque bearer tokens for MCP and extensions — because it avoids external OAuth and supports immediate revocation
- [2026-11-15] D-03 — Bootstrap the single admin account through a first-run /setup page gated by a one-time code printed in backend logs — because it avoids persistent plaintext secrets
- [2026-11-15] D-04 — Use server-side random session IDs stored as SHA-256 hashes in SQLite instead of signed cookies — because it removes SECRET_KEY management and gives immediate logout and revocation
- [2026-11-18] D-05 — Encrypt LLM API profile keys with Fernet using RAGATOOL_ENCRYPTION_KEY or a 0600 key file next to the database — because keys must never be stored or returned in plaintext
- [2026-11-24] D-06 — Agent chat history lives in browser localStorage — because v1 excludes server-side conversation storage and single-user isolation
