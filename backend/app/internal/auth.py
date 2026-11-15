import argparse
import getpass
import hashlib
import hmac
import os
import secrets
import sys
import time
from typing import Optional
from urllib.parse import urlparse

import bcrypt
from fastapi import Depends, HTTPException, Request, Response, status
from fastmcp.server.auth import AccessToken, TokenVerifier

from app.crud import crud_session, crud_token, crud_user
from app.database import create_tables, get_db_connection
from app.internal.rate_limit import SlidingWindowRateLimiter

TOKEN_PREFIX = "ragt_"
SESSION_COOKIE = "ragatool_session"
DEFAULT_ALLOWED_ORIGINS = "http://localhost:4200,http://127.0.0.1:4200"
BCRYPT_MAX_PASSWORD_BYTES = 72

# Throttle failed logins per source address and per (source, username) pair.
LOGIN_IP_LIMITER = SlidingWindowRateLimiter(max_events=20, window_seconds=60)
LOGIN_USER_LIMITER = SlidingWindowRateLimiter(max_events=5, window_seconds=60)

_setup_code: Optional[str] = None
_dummy_password_hash: Optional[str] = None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def get_dummy_password_hash() -> str:
    """A valid hash used to keep failed logins for unknown users slow."""
    global _dummy_password_hash
    if _dummy_password_hash is None:
        _dummy_password_hash = hash_password(secrets.token_urlsafe(16))
    return _dummy_password_hash


def generate_token() -> str:
    return TOKEN_PREFIX + secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_prefix(token: str) -> str:
    return token[:8]


def get_cookie_secure() -> bool:
    return os.getenv("COOKIE_SECURE", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_session_max_age() -> int:
    try:
        hours = int(os.getenv("SESSION_MAX_AGE_HOURS", "168"))
    except ValueError:
        hours = 168
    return max(hours, 1) * 3600


def generate_setup_code() -> str:
    global _setup_code
    _setup_code = secrets.token_urlsafe(16)
    return _setup_code


def clear_setup_code() -> None:
    global _setup_code
    _setup_code = None


def verify_setup_code(code: str) -> bool:
    return _setup_code is not None and hmac.compare_digest(code, _setup_code)


def initialize_auth() -> None:
    """Seed an optional admin from env and print the setup code when needed."""
    with get_db_connection() as db:
        if crud_user.count_users(db) == 0:
            password_hash = os.getenv("RAGATOOL_ADMIN_PASSWORD_HASH")
            if password_hash:
                username = os.getenv("RAGATOOL_ADMIN_USERNAME", "admin")
                crud_user.create_user(db, username, password_hash)
                print(
                    f"INFO: Seeded admin user '{username}' from environment.",
                    flush=True,
                )

        if crud_user.count_users(db) == 0:
            code = generate_setup_code()
            print("RAGATOOL SETUP REQUIRED", flush=True)
            print(f"RAGATOOL SETUP CODE: {code}", flush=True)

        crud_session.delete_expired(db)

    get_dummy_password_hash()


def create_session(user: dict) -> str:
    token = secrets.token_urlsafe(32)
    with get_db_connection() as db:
        crud_session.create_session(
            db,
            user_id=user["id"],
            token_hash=hash_token(token),
            expires_at=int(time.time()) + get_session_max_age(),
            session_version=user["session_version"],
        )
    return token


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=get_session_max_age(),
        httponly=True,
        samesite="lax",
        secure=get_cookie_secure(),
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        SESSION_COOKIE,
        httponly=True,
        samesite="lax",
        secure=get_cookie_secure(),
        path="/",
    )


def delete_current_session(request: Request) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return
    with get_db_connection() as db:
        crud_session.delete_by_hash(db, hash_token(token))


def get_current_user(request: Request) -> Optional[dict]:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None

    token_hash = hash_token(token)
    with get_db_connection() as db:
        session = crud_session.find_by_hash(db, token_hash)
        if session is None:
            return None

        if session["expires_at"] <= int(time.time()):
            crud_session.delete_by_hash(db, token_hash)
            return None

        user = crud_user.get_user_by_id(db, session["user_id"])
        if user is None or user["session_version"] != session["session_version"]:
            crud_session.delete_by_hash(db, token_hash)
            return None

    return {
        "id": user["id"],
        "username": user["username"],
        "session_version": user["session_version"],
    }


def require_user(request: Request) -> dict:
    user = get_current_user(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Cookie"},
        )
    return user


def check_request_origin(request: Request) -> None:
    """Reject cross-site state-changing requests when an Origin is present."""
    origin = request.headers.get("origin")
    if not origin:
        return

    allowed = {
        item.strip()
        for item in os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS).split(",")
        if item.strip()
    }
    if origin in allowed:
        return

    origin_host = urlparse(origin).netloc
    request_host = request.headers.get("host", "")
    if origin_host and request_host and origin_host == request_host:
        return

    raise HTTPException(status_code=403, detail="Origin not allowed")


class DbTokenVerifier(TokenVerifier):
    """Validates opaque API tokens stored as SHA-256 hashes in SQLite."""

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        if not token or not token.startswith(TOKEN_PREFIX):
            return None

        with get_db_connection() as db:
            row = crud_token.find_active_by_hash(db, hash_token(token))
            if row is None:
                return None
            crud_token.touch_token(db, row["id"])

        return AccessToken(
            token=token,
            client_id=row["id"],
            scopes=[],
            claims={"name": row["name"], "prefix": row["prefix"]},
        )


def _prompt_password() -> str:
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.", file=sys.stderr)
        raise SystemExit(1)
    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        raise SystemExit(1)
    if len(password.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        print("Password must be at most 72 bytes.", file=sys.stderr)
        raise SystemExit(1)
    return password


def _cli(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Ragatool auth utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("hash-password", help="Hash a password for env seeding")

    reset = subparsers.add_parser("reset-password", help="Reset the admin password")
    reset.add_argument(
        "--username",
        default=os.getenv("RAGATOOL_ADMIN_USERNAME", "admin"),
    )

    create = subparsers.add_parser(
        "create-token", help="Create an API token and print it once"
    )
    create.add_argument("--name", required=True)

    args = parser.parse_args(argv)
    create_tables()

    if args.command == "hash-password":
        print(hash_password(_prompt_password()))
        return 0

    with get_db_connection() as db:
        if args.command == "reset-password":
            user = crud_user.get_user_by_username(db, args.username)
            if user is None:
                print(f"User '{args.username}' not found.", file=sys.stderr)
                return 1
            crud_user.update_password(db, user["id"], hash_password(_prompt_password()))
            print(f"Password updated for '{args.username}'.")
            return 0

        if args.command == "create-token":
            if crud_user.count_users(db) == 0:
                print(
                    "No admin user exists yet. Complete /setup first.",
                    file=sys.stderr,
                )
                return 1
            token = generate_token()
            crud_token.create_token(
                db, args.name, hash_token(token), token_prefix(token)
            )
            print(token)
            return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
