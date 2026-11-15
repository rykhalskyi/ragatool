import pytest

from app.internal.auth import require_user
from app.main import app


@pytest.fixture(autouse=True)
def bypass_auth_for_existing_tests():
    """Existing API tests predate auth; keep them focused on their own behavior."""
    app.dependency_overrides[require_user] = lambda: {
        "id": "test-user",
        "username": "test",
        "session_version": 1,
    }
    yield
    app.dependency_overrides.pop(require_user, None)
