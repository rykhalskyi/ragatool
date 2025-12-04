# RAGatouille: Local RAG \& MCP Servers Solution

## Project Overview

RAGatouille is a locally deployable solution designed to empower users with their own knowledge base using Retrieval-Augmented Generation (RAG) and a Model Context Protocol (MCP) Server. This project allows you to vectorize various data sources – including books, specifications, documentation, code, and web pages – to create a personalized, local knowledge base. The core unit of organization is a "collection," which can be configured with different embedders and chunking settings to optimize retrieval.

**Note:** This project is currently under active development, and many features are in pre-production.



## Key Features

* **Vectorization of diverse data sources:** Books, specifications, documentation, code, web pages.
* **Collection-based organization:** Manage your knowledge in logical, configurable units.
* **Support for different embedders:** Choose the best embedding model for your specific needs.
* **Configurable chunking settings:** Optimize how your documents are broken down for retrieval.
* **User-friendly interface:** (Implied by frontend components) Easily manage collections and imports.
* **API-driven backend:** Robust and extensible API for programmatic access.
* **Docker/Podman compatibility:** Simple local deployment and management.
* **MCP Server:** Acces from any AI agent

## Getting Started (Local Deployment)

To get started with RAGatouille, you will need Docker or Podman installed on your system or you can run servers locally.

## Build and Run the Containers

1. **Navigate to the project root:**
   Open your terminal or command prompt and navigate to the root directory of the `ragatouille` project, where `docker-compose.yml` is located.
2. **Build the Docker images and run the containers:**
   This command will build the Docker images for both the backend and frontend services based on their respective `Dockerfile`s.

    `bash docker compose up -d --build `

* The FastAPI backend will be accessible externally on `http://localhost:4301`.
* The Angular frontend will be accessible externally on `http://localhost:4300`.
* The MCP Server on `http://localhost:4302/mcp`.


## RAGatouille MCP Configuration

To configure RAGatouille MCP, add the following to your configuration:

```json
"ragatouille": {
      "url": "http://localhost:4302/mcp"
    }
```

## Usage

*(Instructions on how to interact with the application, create collections, import data, and use the RAG/MCP features will go here. This will depend on the final implementation of the UI and API.)*

## Development Status

RAGatouille is an evolving project. While the core functionalities are in place, many features are still under active development and should be considered pre-production. We welcome contributions and feedback from the community.



## License

This project is licensed under the MIT License.

