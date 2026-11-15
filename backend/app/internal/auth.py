import argparse
import getpass
import hashlib
import hmac
import os
import secrets
import sys
from typing import Optional
from urllib.parse import urlparse

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastmcp.server.auth import AccessToken, TokenVerifier

from app.crud import crud_token, crud_user
from app.database import create_tables, get_db_connection

TOKEN_PREFIX = "ragt_"
DEFAULT_ALLOWED_ORIGINS = "http://localhost:4200,http://127.0.0.1:4200"

_setup_code: Optional[str] = None
_secret_key: Optional[str] = None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def generate_token() -> str:
    return TOKEN_PREFIX + secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_prefix(token: str) -> str:
    return token[:8]


def get_secret_key() -> str:
    global _secret_key
    if _secret_key is None:
        configured = os.getenv("SECRET_KEY")
        if configured:
            _secret_key = configured
        else:
            _secret_key = secrets.token_urlsafe(48)
            print(
                "WARNING: SECRET_KEY is not set; sessions will be invalidated on restart.",
                flush=True,
            )
    return _secret_key


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


def set_session(request: Request, user: dict) -> None:
    request.session.clear()
    request.session["user_id"] = user["id"]
    request.session["username"] = user["username"]
    request.session["session_version"] = user["session_version"]


def clear_session(request: Request) -> None:
    request.session.clear()


def get_current_user(request: Request) -> Optional[dict]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    with get_db_connection() as db:
        user = crud_user.get_user_by_id(db, user_id)

    if user is None or user["session_version"] != request.session.get(
        "session_version"
    ):
        request.session.clear()
        return None
    return user


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
