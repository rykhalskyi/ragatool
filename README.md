# Ragatool: Local RAG & MCP Servers Solution

## Project Overview

Ragatool is a locally deployable solution designed to empower users with their own knowledge base using Retrieval-Augmented Generation (RAG) and a Model Context Protocol (MCP) Server. This project allows you to vectorize various data sources – including books, specifications, documentation, code, and web pages – to create a personalized, local knowledge base. The core unit of organization is a "collection," which can be configured with different embedders and chunking settings to optimize retrieval.

All 3rd party integrations (OnlyOffice, Mozilla Thunderbird, Microsoft Outlook) connect to Ragatool through a single unified MCP server interface using WebSocket communication.

**Note:** This project is currently under active development, and many features are in pre-production.

## Key Features

- **Vectorization of diverse data sources:** Books, specifications, documentation, code, web pages.
- **Collection-based organization:** Manage your knowledge in logical, configurable units.
- **Support for different embedders:** Choose the best embedding model for your specific needs.
- **Configurable chunking settings:** Optimize how your documents are broken down for retrieval.
- **User-friendly interface:** Easily manage collections and imports.
- **API-driven backend:** Robust and extensible API for programmatic access.
- **Docker/Podman compatibility:** Simple local deployment and management.
- **Unified MCP Server:** Access from any AI agent through a single MCP endpoint.
- **3rd Party Integrations:** Seamless integration with popular desktop applications.

## Getting Started (Local Deployment)

To get started with Ragatool, you will need Docker or Podman installed on your system or you can run servers locally.

### Build and Run the Containers

1. **Navigate to the project root:**
   Open your terminal or command prompt and navigate to the root directory of the `Ragatool` project, where `docker-compose.yml` is located.
2. **Build the Docker images and run the containers:**
   This command will build the Docker images for both the backend and frontend services based on their respective `Dockerfile`s.

   `docker compose up -d --build`

### Running with Pre-built Images (GHCR)

You can also run Ragatool using the pre-built images hosted on GitHub Container Registry. 

1. **Create or update a `docker-compose.ghcr.yml` file:**

```yaml
version: '3.8'

services:
  backend:
    image: ghcr.io/rykhalskyi/ragatool-backend:latest
    ports:
      - "4301:8000"
      - "4302:8001"
      - "4303:8002"
    env_file:
      - backend/.env
    environment:
      PYTHONUNBUFFERED: 1
      ALLOWED_ORIGINS: http://localhost:4300
      MCP_HOST: "0.0.0.0"
      MCP_PORT: "8001"

  frontend:
    image: ghcr.io/rykhalskyi/ragatool-frontend:latest
    environment:
      # Browser calls the same origin; nginx proxies /api to the backend.
      API_URL: /api
      BACKEND_URL: http://backend:8000
    ports:
      - "4300:80"
    depends_on:
      - backend
```

2. **Run the containers:**

   `docker compose -f docker-compose.ghcr.yml --env-file backend/.env up -d`

The frontend image is not tied to an API address at build time. At container
start it writes `/config.js` from `API_URL`, and nginx renders its `/api/` proxy
from `BACKEND_URL`, so the same image works on any host or in Kubernetes. Set
`API_URL` to the URL the browser should call (default `/api`, same origin) and
`BACKEND_URL` to the backend service address nginx should proxy to.

- **FastAPI backend:** `http://localhost:4301`
- **Angular frontend:** `http://localhost:4300`
- **MCP Server:** `http://localhost:4302/mcp`

## Authentication

The first time the backend starts against an empty database it prints a
one-time setup code to its logs:

```bash
docker compose logs backend | grep 'SETUP CODE'
```

Open the UI and set the admin username and password on the setup screen. The
code is only required once. After that, sign in with the username and password.

API tokens for MCP clients and extension WebSockets are managed on the
**Access** page. Tokens are shown only once; revoking one takes effect
immediately.

Sessions are stored server-side in SQLite and referenced by an `HttpOnly`
cookie, so they survive restarts and can be revoked immediately. Use
`COOKIE_SECURE=true` when serving over HTTPS.

## Public deployment (Cloudflare Tunnel)

Ragatool can be exposed through a Cloudflare Tunnel, but do not publish it
directly. Recommended setup:

1. **Complete `/setup` locally first**, then start the tunnel.
2. **Put Cloudflare Access in front of the hostname** and allow only your
   identity/group. Treat Cloudflare Access as the first gate and the Ragatool
   login as the second.
3. **Route only the frontend** through the tunnel. Do not expose backend
   ports `4301`, `4302`, or `4303`; they stay on the LAN/VPN.
4. Set:
   ```dotenv
   ALLOWED_ORIGINS=https://ragatool.example.com
   COOKIE_SECURE=true
   ENABLE_API_DOCS=false
   ```
5. Add Cloudflare WAF rate limits for `/api/auth/login` and
   `/api/auth/setup` (for example, 5 requests per minute per IP).
6. Enable HSTS and the managed WAF rules at Cloudflare.
7. Keep MCP and extension WebSockets off the public hostname. If remote
   clients need them, use a separate hostname protected by Cloudflare Access
   service tokens **and** the Ragatool bearer token. Browser WebSocket
   plugins pass the token in `?token=`, which can appear in proxy logs.

Minimal `cloudflared` ingress (frontend only):

```yaml
tunnel: <tunnel-id>
credentials-file: /etc/cloudflared/<tunnel-id>.json
ingress:
  - hostname: ragatool.example.com
    service: http://localhost:4300
  - service: http_status:404
```

The frontend container proxies `/api` to the backend, so the UI stays
same-origin and the session cookie uses `SameSite=Lax`. The bundled nginx adds
CSP and other security headers; the CSP assumes `API_URL=/api` (same origin).

## Ragatool MCP Configuration

Every MCP request requires an API token from the Access page. Add it to your
client configuration as a bearer header:

1. SSE:

```json
"Ragatool": {
      "url": "http://localhost:4302/mcp",
      "headers": { "Authorization": "Bearer ragt_..." }
    }
```
2. HTTP:

```json
"Ragatool": {
      "url": "http://localhost:4303/mcp",
      "headers": { "Authorization": "Bearer ragt_..." }
    }
```

## 3rd Party Integrations

Ragatool provides plugins for popular desktop applications, enabling AI agents to interact with your data across different platforms. All plugins communicate with the Ragatool server via WebSocket at `ws://localhost:8000/extensions/ws` and require an API token from the Access page.

- Browser-based plugins (OnlyOffice, Thunderbird) pass the token as the
  `?token=` query parameter.
- The Outlook add-in reads the `RAGATOUL_TOKEN` environment variable and uses
  it the same way.

### OnlyOffice Plugin

Located in `plugins/onlyoffice/`

The Ragatool OnlyOffice Plugin enables direct integration with the OnlyOffice text editor. This allows users to:
- Connect OnlyOffice with the Ragatool RAG system.
- Read and modify DOCX documents directly within the OnlyOffice editor, leveraging Ragatool's knowledge base.
- Provides AI agent access to documents through the unified MCP server interface.

### Mozilla Thunderbird Plugin

Located in `plugins/thunderbird/`

A WebExtension that connects Mozilla Thunderbird to the Ragatool server. Available commands:
- `account_list` - Get list of all configured email accounts
- `email_query` - Search messages by subject, author, date, read status, attachments, and more
- `get_full_message` - Retrieve full message details including headers and MIME parts

### Microsoft Outlook Plugin

Located in `plugins/outlook/`

A C# AddIn that integrates Microsoft Outlook with Ragatool. Provides similar functionality to the Thunderbird plugin, enabling AI agents to:
- Access email accounts
- Query and search emails
- Retrieve full message content

## Architecture

All plugins use a unified WebSocket-based command protocol:
```
Client (Plugin) <--WebSocket--> Ragatool Server <---> MCP <---> AI Agent
```

This architecture allows any AI agent to interact with multiple desktop applications through a single MCP server endpoint.

## Development Status

Ragatool is an evolving project. While the core functionalities are in place, many features are still under active development and should be considered pre-production. We welcome contributions and feedback from the community.

## License

This project is licensed under the MIT License.
