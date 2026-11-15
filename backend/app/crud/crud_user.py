import sqlite3
import uuid
from typing import Optional


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
    return dict(row) if row is not None else None


def count_users(db: sqlite3.Connection) -> int:
    row = db.execute("SELECT COUNT(*) AS count FROM auth_users").fetchone()
    return int(row["count"]) if row else 0


def create_user(db: sqlite3.Connection, username: str, password_hash: str) -> dict:
    user_id = uuid.uuid4().hex
    db.execute(
        "INSERT INTO auth_users (id, username, password_hash) VALUES (?, ?, ?)",
        (user_id, username, password_hash),
    )
    db.commit()
    user = get_user_by_id(db, user_id)
    if user is None:
        raise RuntimeError("Failed to create user")
    return user


def create_first_user(
    db: sqlite3.Connection, username: str, password_hash: str
) -> Optional[dict]:
    """Atomically create the only user. Returns None if a user already exists."""
    user_id = uuid.uuid4().hex
    try:
        cursor = db.execute(
            "INSERT INTO auth_users (id, username, password_hash) "
            "SELECT ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM auth_users)",
            (user_id, username, password_hash),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return None
    if cursor.rowcount == 0:
        return None
    return get_user_by_id(db, user_id)


def get_user_by_id(db: sqlite3.Connection, user_id: str) -> Optional[dict]:
    row = db.execute(
        "SELECT id, username, password_hash, session_version, created_at "
        "FROM auth_users WHERE id = ?",
        (user_id,),
    ).fetchone()
    return _row_to_dict(row)


def get_user_by_username(db: sqlite3.Connection, username: str) -> Optional[dict]:
    row = db.execute(
        "SELECT id, username, password_hash, session_version, created_at "
        "FROM auth_users WHERE username = ?",
        (username,),
    ).fetchone()
    return _row_to_dict(row)


def update_password(db: sqlite3.Connection, user_id: str, password_hash: str) -> bool:
    cursor = db.execute(
        "UPDATE auth_users "
        "SET password_hash = ?, session_version = session_version + 1 "
        "WHERE id = ?",
        (password_hash, user_id),
    )
    db.commit()
    return cursor.rowcount > 0
