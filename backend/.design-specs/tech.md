# Technology Stack

## Project Type
This project is a web API service designed to manage collections of documents, process them into chunks, generate embeddings, and provide a search interface.

## Core Technologies

### Primary Language(s)
- **Language**: Python 3.12
- **Runtime/Compiler**: CPython
- **Language-specific tools**: pip for package management.

### Key Dependencies/Libraries
- **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.
- **Uvicorn**: An ASGI server, for running the FastAPI application.
- **ChromaDB**: An open-source embedding database for building AI applications.
- **Sentence-Transformers**: A Python framework for state-of-the-art sentence, text and image embeddings.
- **SQLAlchemy**: The Python SQL Toolkit and Object Relational Mapper. Used for database interactions.
- **Pydantic**: Data validation and settings management using Python type annotations.

### Application Architecture
The application follows a client-server architecture. It is structured by layers, separating concerns into:
- **Routers**: Defines the API endpoints.
- **CRUD**: Contains the logic for Create, Read, Update, and Delete operations on the database.
- **Models**: Business logic and data structures.
- **Schemas**: Pydantic models for data validation of API requests and responses.
- **Internal**: Contains internal logic, such as the MCP (Mission Control Protocol) Manager and a Message Hub for real-time communication.

### Data Storage (if applicable)
- **Primary storage**: SQLite is used as the relational database for storing metadata about collections.
- **Vector storage**: ChromaDB is used to store vector embeddings of the documents.

### External Integrations (if applicable)
- **APIs**: The application provides a RESTful API.
- **Protocols**: HTTP/REST.

## Development Environment

### Build & Development Tools
- **Package Management**: pip is used for managing Python packages.
- **Development workflow**: The application can be run directly with Uvicorn for local development.

### Code Quality Tools
- **Typing**: The codebase uses Python's standard type hints for static analysis and code clarity.

### Version Control & Collaboration
- **VCS**: Git

## Deployment & Distribution (if applicable)
- **Target Platform(s)**: The application is designed to be deployed in a containerized environment using Docker.
- **Distribution Method**: The application is distributed as a Docker image.
- **Installation Requirements**: Docker and Python 3.12.
- **Update Mechanism**: By deploying a new version of the Docker image.
