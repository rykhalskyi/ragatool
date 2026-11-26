from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

import app.database as database
from app.internal.agent import llm_client, service
from app.routers import agent
from app.schemas.agent import AgentChatResponse, AgentUsage


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_URL", str(tmp_path / "agent.db"))
    monkeypatch.setenv("RAGATOOL_ENCRYPTION_KEY", Fernet.generate_key().decode())
    database.create_tables()

    test_app = FastAPI()
    test_app.include_router(agent.router, prefix="/agent")

    with TestClient(test_app) as test_client:
        yield test_client


def create_profile(client):
    response = client.post(
        "/agent/profiles",
        json={
            "name": "Mock",
            "provider": "openai",
            "base_url": "https://example.invalid/v1",
            "api_key": "sk-secret-1234",
            "model": "mock-model",
            "temperature": 0.2,
            "max_tokens": 512,
            "connect_timeout_seconds": 5,
            "read_timeout_seconds": 5,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_chat_requires_an_active_profile(client):
    response = client.post("/agent/chat", json={"message": "hello"})

    assert response.status_code == 400
    assert "Settings" in response.json()["detail"]


def test_chat_returns_agent_response(client, monkeypatch):
    create_profile(client)

    async def fake_run_chat(db, request):
        return AgentChatResponse(
            message=f"Echo: {request.message}",
            model="mock-model",
            tool_calls=[],
            usage=AgentUsage(total_tokens=12),
            warnings=[],
        )

    monkeypatch.setattr(service, "run_chat", fake_run_chat)

    response = client.post("/agent/chat", json={"message": "hello"})

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Echo: hello"
    assert body["usage"]["total_tokens"] == 12


@pytest.mark.parametrize(
    ("kind", "expected_status"),
    [("auth", 400), ("rate_limit", 429), ("timeout", 502), ("network", 502)],
)
def test_chat_maps_provider_errors(client, monkeypatch, kind, expected_status):
    create_profile(client)

    async def fake_run_chat(db, request):
        raise llm_client.LlmProviderError(kind, "friendly message")

    monkeypatch.setattr(service, "run_chat", fake_run_chat)

    response = client.post("/agent/chat", json={"message": "hello"})

    assert response.status_code == expected_status
    assert response.json()["detail"] == "friendly message"


def test_chat_rejects_blank_message(client):
    response = client.post("/agent/chat", json={"message": "   "})

    assert response.status_code == 422


def test_chat_never_returns_api_key(client, monkeypatch):
    create_profile(client)

    async def fake_run_chat(db, request):
        return AgentChatResponse(message="done", model="mock-model", warnings=[])

    monkeypatch.setattr(service, "run_chat", fake_run_chat)

    response = client.post("/agent/chat", json={"message": "hello"})

    assert "sk-secret-1234" not in response.text
    assert "api_key" not in response.text
