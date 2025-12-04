# Project Structure

## Directory Organization

```
app/
├── crud/                   # Contains Create, Read, Update, Delete (CRUD) operations for database models.
├── internal/               # Core internal logic and managers (e.g., background tasks, MCP).
├── models/                 # Business logic models and data processing classes.
├── routers/                # FastAPI routers that define API endpoints.
├── schemas/                # Pydantic schemas for data validation and serialization.
├── __init__.py             # Initializes the 'app' package.
├── database.py             # Database connection and table creation logic.
├── dependencies.py         # FastAPI dependency injection functions.
└── main.py                 # Main application entry point, FastAPI app instantiation, and middleware.
```

## Naming Conventions

### Files
- **Modules**: `snake_case.py` (e.g., `crud_collection.py`, `background_task_dispatcher.py`).

### Code
- **Classes**: `PascalCase` (e.g., `Collection`, `FileImport`).
- **Functions/Methods**: `snake_case` (e.g., `get_collections`, `import_data`).
- **Constants**: There is no explicit convention for constants, but variables that hold constant values are typically `snake_case` (e.g., `allowed_origins`).
- **Variables**: `snake_case` (e.g., `db_collection`, `text_content`).

## Import Patterns

### Import Order
The import order is not strictly enforced, but generally follows this pattern:
1. Standard library modules (e.g., `os`, `threading`, `json`).
2. Third-party/external dependencies (e.g., `fastapi`, `chromadb`, `pydantic`).
3. Internal application modules, using absolute paths from the `app` root (e.g., `from app.crud.crud_log import delete_log_by_collection_id`).

### Module/Package Organization
- Imports are absolute from the project root (`app`), which makes the code more readable and less prone to errors.
- Relative imports are not used.

## Code Structure Patterns

### Module/Class Organization
A common pattern observed in files is:
1.  Imports.
2.  Router instantiation (in router files).
3.  Class or function definitions.

### Function/Method Organization
- Functions are generally short and focused on a single task.
- FastAPI's dependency injection system (`Depends`) is used to manage dependencies like database connections.

## Code Organization Principles

1.  **Single Responsibility**: Each module has a clear purpose (e.g., `crud` for database operations, `routers` for API endpoints).
2.  **Modularity**: The code is organized into distinct modules, promoting reusability and separation of concerns.
3.  **Testability**: The use of dependency injection makes the code easier to test.
