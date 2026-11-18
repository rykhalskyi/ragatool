from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

import app.database as database
from app.internal.agent.crypto import decrypt_api_key
from app.internal.agent import llm_client
from app.routers import agent
from app.schemas.agent import LlmProfileTestResult


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_URL", str(tmp_path / "agent.db"))
    monkeypatch.setenv("RAGATOOL_ENCRYPTION_KEY", Fernet.generate_key().decode())
    database.create_tables()

    test_app = FastAPI()
    test_app.include_router(agent.router, prefix="/agent")

    with TestClient(test_app) as test_client:
        yield test_client


def create_profile(client, **overrides):
    payload = {
        "name": "DeepSeek",
        "provider": "deepseek",
        "base_url": "https://api.deepseek.com",
        "api_key": "sk-secret-1234",
        "model": "deepseek-chat",
        "temperature": 0.2,
        "max_tokens": 2048,
        "connect_timeout_seconds": 30,
        "read_timeout_seconds": 120,
    }
    payload.update(overrides)
    return client.post("/agent/profiles", json=payload)


def test_providers_include_presets(client):
    response = client.get("/agent/providers")
    assert response.status_code == 200
    ids = {provider["id"] for provider in response.json()}
    assert {"openai", "deepseek", "siliconflow", "openrouter", "custom"} <= ids


def test_create_profile_encrypts_and_masks_key(client):
    response = create_profile(client)
    assert response.status_code == 201

    body = response.json()
    assert body["api_key_masked"].endswith("1234")
    assert "sk-secret-1234" not in response.text
    assert "api_key" not in body
    assert body["is_active"] is True

    with database.get_db_connection() as db:
        row = db.execute("SELECT api_key FROM llm_profiles").fetchone()
    assert row["api_key"] != "sk-secret-1234"
    assert decrypt_api_key(row["api_key"]) == "sk-secret-1234"


def test_first_profile_is_active_and_activation_is_exclusive(client):
    first = create_profile(client, name="First", is_active=False).json()
    second = create_profile(client, name="Second", is_active=False).json()
    assert first["is_active"] is True
    assert second["is_active"] is False

    activated = client.post(
        f"/agent/profiles/{second['id']}/activate", json={"active": True}
    )
    assert activated.status_code == 200
    assert activated.json()["is_active"] is True

    profiles = client.get("/agent/profiles").json()
    by_name = {profile["name"]: profile for profile in profiles}
    assert by_name["First"]["is_active"] is False
    assert by_name["Second"]["is_active"] is True


def test_update_without_api_key_keeps_the_stored_key(client):
    profile = create_profile(client).json()

    updated = client.patch(
        f"/agent/profiles/{profile['id']}",
        json={"name": "Renamed", "api_key": "", "max_tokens": 4096},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Renamed"
    assert updated.json()["max_tokens"] == 4096
    assert updated.json()["api_key_masked"].endswith("1234")

    with database.get_db_connection() as db:
        row = db.execute(
            "SELECT api_key FROM llm_profiles WHERE id = ?", (profile["id"],)
        ).fetchone()
    assert decrypt_api_key(row["api_key"]) == "sk-secret-1234"


def test_update_with_new_api_key_reencrypts(client):
    profile = create_profile(client).json()

    updated = client.patch(
        f"/agent/profiles/{profile['id']}", json={"api_key": "sk-new-key-9999"}
    )
    assert updated.status_code == 200
    assert updated.json()["api_key_masked"].endswith("9999")

    with database.get_db_connection() as db:
        row = db.execute(
            "SELECT api_key FROM llm_profiles WHERE id = ?", (profile["id"],)
        ).fetchone()
    assert decrypt_api_key(row["api_key"]) == "sk-new-key-9999"


def test_rejects_invalid_base_url(client):
    response = create_profile(client, base_url="ftp://example.com")
    assert response.status_code == 422


def test_delete_profile(client):
    profile = create_profile(client).json()

    deleted = client.delete(f"/agent/profiles/{profile['id']}")
    assert deleted.status_code == 204
    assert client.get("/agent/profiles").json() == []

    missing = client.delete(f"/agent/profiles/{profile['id']}")
    assert missing.status_code == 404


def test_test_endpoint_returns_provider_result(client, monkeypatch):
    profile = create_profile(client).json()

    async def fake_test_connection(profile, api_key):
        assert profile["id"] == profile_id
        assert api_key == "sk-secret-1234"
        return LlmProfileTestResult(
            ok=True, message="Connection successful.", model="deepseek-chat", latency_ms=12
        )

    profile_id = profile["id"]
    monkeypatch.setattr(llm_client, "test_connection", fake_test_connection)

    response = client.post(f"/agent/profiles/{profile_id}/test")
    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "message": "Connection successful.",
        "model": "deepseek-chat",
        "latency_ms": 12,
    }
