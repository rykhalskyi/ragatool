import asyncio
import logging
import queue

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.datastructures import Headers, QueryParams
from starlette.requests import Request
from starlette.websockets import WebSocketDisconnect

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
from app.internal.log_redaction import SensitiveQueryFilter, redact_sensitive
from app.routers import auth, tokens
from app.routers.extensions import (
    WS_SUBPROTOCOL,
    _extract_ws_credentials,
    _is_valid_ws_token,
)


class FakeWebSocket:
    def __init__(self, headers=None, query_params=None):
        self.headers = Headers(headers or {})
        self.query_params = QueryParams(query_params or {})


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_URL", str(tmp_path / "auth.db"))
    database.create_tables()
    auth_core.clear_setup_code()
    auth_core.LOGIN_IP_LIMITER.clear()
    auth_core.LOGIN_USER_LIMITER.clear()

    test_app = FastAPI()
    test_app.include_router(auth.router, prefix="/auth")
    test_app.include_router(tokens.router, prefix="/tokens")

    with TestClient(test_app) as test_client:
        yield test_client

    auth_core.clear_setup_code()
    auth_core.LOGIN_IP_LIMITER.clear()
    auth_core.LOGIN_USER_LIMITER.clear()


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


def test_login_is_rate_limited(client):
    complete_setup(client, password="correct-password")

    for _ in range(4):
        wrong = client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrong-password"},
        )
        assert wrong.status_code == 401

    # A successful login resets the per-user bucket but keeps the IP bucket.
    ok = client.post(
        "/auth/login",
        json={"username": "admin", "password": "correct-password"},
    )
    assert ok.status_code == 200

    for _ in range(5):
        wrong = client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrong-password"},
        )
        assert wrong.status_code == 401

    blocked = client.post(
        "/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1
    assert blocked.json()["detail"] == "Too many login attempts. Try again later."


def test_login_failures_are_indistinguishable(client):
    complete_setup(client, password="correct-password")

    unknown = client.post(
        "/auth/login",
        json={"username": "nobody", "password": "whatever-password"},
    )
    wrong = client.post(
        "/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


def test_setup_rejects_blank_username(client):
    code = auth_core.generate_setup_code()
    response = client.post(
        "/auth/setup",
        json={
            "username": "   ",
            "password": "password123",
            "setup_code": code,
        },
    )
    assert response.status_code == 422


def test_setup_rejects_password_over_bcrypt_limit(client):
    code = auth_core.generate_setup_code()
    response = client.post(
        "/auth/setup",
        json={
            "username": "admin",
            "password": "é" * 40,  # 80 UTF-8 bytes
            "setup_code": code,
        },
    )
    assert response.status_code == 422


def test_token_name_rejects_blank(client):
    complete_setup(client)
    response = client.post("/tokens", json={"name": "   "})
    assert response.status_code == 422


def test_current_user_never_exposes_password_hash(client):
    complete_setup(client)
    token = client.cookies.get(auth_core.SESSION_COOKIE)
    request = Request(
        {
            "type": "http",
            "headers": [
                (b"cookie", f"{auth_core.SESSION_COOKIE}={token}".encode())
            ],
        }
    )

    user = auth_core.get_current_user(request)

    assert user is not None
    assert set(user) == {"id", "username", "session_version"}


def test_ws_credentials_from_subprotocol():
    websocket = FakeWebSocket(
        headers={"sec-websocket-protocol": f"{WS_SUBPROTOCOL}, ragt_subprotocol"}
    )
    assert _extract_ws_credentials(websocket) == ("ragt_subprotocol", WS_SUBPROTOCOL)


def test_ws_credentials_from_authorization_header():
    websocket = FakeWebSocket(headers={"authorization": "Bearer ragt_header"})
    assert _extract_ws_credentials(websocket) == ("ragt_header", None)


def test_ws_credentials_ignore_query_token():
    websocket = FakeWebSocket(query_params={"token": "ragt_in_query"})
    assert _extract_ws_credentials(websocket) == (None, None)


def test_ws_token_requires_expected_prefix():
    assert not _is_valid_ws_token("not-a-ragatool-token")


def test_sensitive_query_values_are_redacted():
    assert (
        redact_sensitive("/extensions/ws?token=ragt_secret&x=1")
        == "/extensions/ws?token=***&x=1"
    )

    record = logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        "",
        0,
        '%s - "%s %s %s" %d',
        ("1.2.3.4", "GET", "/extensions/ws?token=ragt_secret", "HTTP/1.1", 200),
        None,
    )
    SensitiveQueryFilter().filter(record)
    assert "ragt_secret" not in str(record.args)


class FakeExtensionManager:
    def register_client(self):
        return "test-client", queue.Queue()

    def unregister_client(self, client_id):
        return None

    def process_incoming_message(self, client_id, data):
        return None


def _ws_app():
    from app.dependencies import get_extension_manager
    from app.routers import extensions

    test_app = FastAPI()
    test_app.include_router(extensions.router, prefix="/extensions")
    test_app.dependency_overrides[get_extension_manager] = FakeExtensionManager
    return test_app


def test_websocket_accepts_subprotocol_token(client):
    complete_setup(client)
    token = generate_token()
    with database.get_db_connection() as db:
        crud_token.create_token(db, "plugin", hash_token(token), token_prefix(token))

    with TestClient(_ws_app()) as ws_client:
        with ws_client.websocket_connect(
            "/extensions/ws", subprotocols=[WS_SUBPROTOCOL, token]
        ) as websocket:
            assert websocket.accepted_subprotocol == WS_SUBPROTOCOL


def test_websocket_rejects_query_token(client):
    complete_setup(client)
    token = generate_token()
    with database.get_db_connection() as db:
        crud_token.create_token(db, "plugin", hash_token(token), token_prefix(token))

    with TestClient(_ws_app()) as ws_client:
        with pytest.raises(WebSocketDisconnect):
            with ws_client.websocket_connect(f"/extensions/ws?token={token}"):
                pass
