import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.database as database
from app.crud import crud_token, crud_user
from app.internal import auth as auth_core
from app.internal.auth import (
    DbTokenVerifier,
    generate_token,
    hash_password,
    hash_token,
    token_prefix,
    verify_password,
)
from app.routers import auth, tokens
from app.routers.extensions import _is_valid_ws_token


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_URL", str(tmp_path / "auth.db"))
    database.create_tables()
    auth_core.clear_setup_code()

    test_app = FastAPI()
    test_app.include_router(auth.router, prefix="/auth")
    test_app.include_router(tokens.router, prefix="/tokens")

    with TestClient(test_app) as test_client:
        yield test_client

    auth_core.clear_setup_code()


def complete_setup(client: TestClient, username="admin", password="password123"):
    code = auth_core.generate_setup_code()
    response = client.post(
        "/auth/setup",
        json={
            "username": username,
            "password": password,
            "setup_code": code,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_setup_flow_requires_one_time_code(client):
    code = auth_core.generate_setup_code()

    assert client.get("/auth/status").json() == {"initialized": False}

    bad = client.post(
        "/auth/setup",
        json={
            "username": "admin",
            "password": "password123",
            "setup_code": "wrong",
        },
    )
    assert bad.status_code == 400

    ok = client.post(
        "/auth/setup",
        json={
            "username": "admin",
            "password": "password123",
            "setup_code": code,
        },
    )
    assert ok.status_code == 200
    assert ok.json()["username"] == "admin"
    assert client.get("/auth/status").json() == {"initialized": True}

    again = client.post(
        "/auth/setup",
        json={
            "username": "other",
            "password": "password123",
            "setup_code": code,
        },
    )
    assert again.status_code == 409


def test_login_logout_and_session(client):
    complete_setup(client, password="correct-password")
    client.post("/auth/logout")
    assert client.get("/auth/me").status_code == 401

    wrong = client.post(
        "/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )
    assert wrong.status_code == 401

    login = client.post(
        "/auth/login",
        json={"username": "admin", "password": "correct-password"},
    )
    assert login.status_code == 200
    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "admin"


def test_logout_deletes_server_side_session(client):
    complete_setup(client)

    with database.get_db_connection() as db:
        count = db.execute("SELECT COUNT(*) AS count FROM sessions").fetchone()["count"]
    assert count == 1

    client.post("/auth/logout")

    with database.get_db_connection() as db:
        count = db.execute("SELECT COUNT(*) AS count FROM sessions").fetchone()["count"]
    assert count == 0


def test_password_hashing_round_trip():
    password_hash = hash_password("password123")
    assert verify_password("password123", password_hash)
    assert not verify_password("password124", password_hash)


def test_token_crud_and_revocation(client):
    complete_setup(client)

    created = client.post("/tokens", json={"name": "opencode"})
    assert created.status_code == 200
    payload = created.json()
    assert payload["token"].startswith("ragt_")
    assert payload["prefix"] == payload["token"][:8]

    listed = client.get("/tokens")
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 1
    assert "token" not in rows[0]
    assert "token_hash" not in rows[0]

    revoked = client.delete(f"/tokens/{payload['id']}")
    assert revoked.status_code == 204
    assert client.get("/tokens").json()[0]["revoked_at"] is not None
    assert client.delete(f"/tokens/{payload['id']}").status_code == 404


def test_tokens_require_a_session(client):
    assert client.get("/tokens").status_code == 401
    assert client.post("/tokens", json={"name": "opencode"}).status_code == 401


def test_db_token_verifier_accepts_and_rejects(client):
    complete_setup(client)

    token = generate_token()
    with database.get_db_connection() as db:
        row = crud_token.create_token(
            db, "mcp", hash_token(token), token_prefix(token)
        )

    verifier = DbTokenVerifier()
    accepted = asyncio.run(verifier.verify_token(token))
    assert accepted is not None
    assert accepted.client_id == row["id"]
    assert asyncio.run(verifier.verify_token("ragt_invalid")) is None

    with database.get_db_connection() as db:
        crud_token.revoke_token(db, row["id"])
    assert asyncio.run(verifier.verify_token(token)) is None


def test_extension_ws_token_check(client):
    complete_setup(client)

    token = generate_token()
    with database.get_db_connection() as db:
        row = crud_token.create_token(
            db, "plugin", hash_token(token), token_prefix(token)
        )

    assert _is_valid_ws_token(token)
    assert not _is_valid_ws_token("ragt_invalid")
    assert not _is_valid_ws_token(None)

    with database.get_db_connection() as db:
        crud_token.revoke_token(db, row["id"])
    assert not _is_valid_ws_token(token)


def test_initialize_auth_seeds_from_env(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_URL", str(tmp_path / "seed.db"))
    monkeypatch.setenv("RAGATOOL_ADMIN_PASSWORD_HASH", hash_password("password123"))
    monkeypatch.setenv("RAGATOOL_ADMIN_USERNAME", "seeded")
    database.create_tables()
    auth_core.clear_setup_code()

    auth_core.initialize_auth()

    with database.get_db_connection() as db:
        assert crud_user.count_users(db) == 1
        user = crud_user.get_user_by_username(db, "seeded")
        assert user is not None
        assert verify_password("password123", user["password_hash"])
