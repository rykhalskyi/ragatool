# Code Style and Best Practices

This document outlines the primary code style conventions and architectural patterns used in this project. The goal is to maintain a clean, consistent, and maintainable codebase.

---

# Foundational Principles

The project implicitly follows several software engineering principles:

*   **KISS (Keep It Simple, Stupid):** The overall architecture and implementation favor straightforward solutions over complex ones.
*   **DRY (Don't Repeat Yourself):** Logic is centralized where possible (e.g., in CRUD modules), but there are opportunities for further refactoring to reduce duplication.
*   **Separation of Concerns:** The project is well-structured, with a clear separation between API routes (`routers`), data access logic (`crud`), business models (`models`), and data schemas (`schemas`).

---

# Specific Guidelines

## Guideline: Dependency Injection for Reusability and Testing

**Problem:**
Directly instantiating dependencies like database connections or shared services within endpoint functions makes the code tightly coupled and difficult to test in isolation.

```python
# What to avoid
@router.get("/items")
def read_items():
    db = get_db_connection() # Direct instantiation
    items = get_all_items(db)
    db.close()
    return items
```

**Recommendation:**
Use FastAPI's dependency injection system (`Depends`) to provide dependencies to path operation functions. This decouples the endpoint logic from the dependency's creation and management.

1.  **Define a dependency provider function:** This function is responsible for creating and yielding the dependency.
    ```python
    # in app/dependencies.py
    def get_db():
        db = get_db_connection()
        try:
            yield db
        finally:
            db.close()
    ```
2.  **Inject the dependency into the endpoint function:**
    ```python
    # in a router file
    from app.dependencies import get_db

    @router.get("/collections/", response_model=List[Collection])
    def read_collections(db: Connection = Depends(get_db)):
        return get_collections(db)
    ```

**Rationale:**
This approach makes the code more modular, reusable, and significantly easier to test. During testing, you can override the dependency with a mock or a test-specific version without changing the endpoint's code.

---

## Guideline: Typed and Validated Data Models with Pydantic

**Problem:**
Passing raw dictionaries or untyped objects between API layers and within the application can lead to runtime errors, inconsistent data structures, and a poor developer experience.

**Recommendation:**
Define clear, typed data models using Pydantic for all API inputs and outputs. These models serve as the single source of truth for the data's structure and validation rules.

1.  **Define a schema:** Create a Pydantic model in the `app/schemas/` directory.
    ```python
    # in app/schemas/collection.py
    from pydantic import BaseModel

    class Collection(BaseModel):
        id: str
        name: str
        description: Optional[str] = None
        enabled: bool = True
    ```
2.  **Use the schema in API endpoints:** Apply the model as a type hint in FastAPI path operations to get automatic request body validation and response serialization.
    ```python
    # in a router file
    @router.post("/", response_model=Collection)
    def create_new_collection(collection: CollectionCreate, db: Connection = Depends(get_db)):
        # 'collection' is a validated Pydantic model
        return create_collection(db, collection)
    ```

**Rationale:**
Using Pydantic schemas provides automatic data validation, reduces boilerplate code, improves API documentation (in OpenAPI/Swagger UI), and enhances code clarity and maintainability by providing a clear, self-documenting data contract.

---

## Guideline: Consistent Naming Conventions

**Problem:**
Inconsistent naming for files, variables, functions, and classes makes the code harder to read, navigate, and understand.

**Recommendation:**
Adhere to the following PEP 8-inspired naming conventions throughout the project:

*   **Files/Modules:** `snake_case.py` (e.g., `crud_collection.py`).
*   **Classes:** `PascalCase` (e.g., `MessageHub`, `CollectionCreate`).
*   **Functions/Methods:** `snake_case()` (e.g., `get_collections`, `create_chunks`).
*   **Variables:** `snake_case` (e.g., `db_collection`, `text_content`).

**Rationale:**
A consistent naming scheme makes the code predictable and easier to read. It allows developers to quickly infer the type and purpose of an object based on its name.
