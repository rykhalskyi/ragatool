import sqlite3
import time
import uuid
from typing import Optional

SESSION_COLUMNS = "id, user_id, created_at, expires_at, session_version"


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
    return dict(row) if row is not None else None


def create_session(
    db: sqlite3.Connection,
    user_id: str,
    token_hash: str,
    expires_at: int,
    session_version: int,
) -> dict:
    session_id = uuid.uuid4().hex
    now = int(time.time())
    db.execute(
        "INSERT INTO sessions "
        "(id, user_id, token_hash, created_at, expires_at, session_version) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, user_id, token_hash, now, expires_at, session_version),
    )
    db.commit()
    row = db.execute(
        f"SELECT {SESSION_COLUMNS} FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    result = _row_to_dict(row)
    if result is None:
        raise RuntimeError("Failed to create session")
    return result


def find_by_hash(db: sqlite3.Connection, token_hash: str) -> Optional[dict]:
    row = db.execute(
        f"SELECT {SESSION_COLUMNS} FROM sessions WHERE token_hash = ?",
        (token_hash,),
    ).fetchone()
    return _row_to_dict(row)


def delete_by_hash(db: sqlite3.Connection, token_hash: str) -> bool:
    cursor = db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
    db.commit()
    return cursor.rowcount > 0


def delete_for_user(db: sqlite3.Connection, user_id: str) -> int:
    cursor = db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    db.commit()
    return cursor.rowcount


def delete_expired(db: sqlite3.Connection, now: Optional[int] = None) -> int:
    cutoff = int(time.time()) if now is None else now
    cursor = db.execute("DELETE FROM sessions WHERE expires_at <= ?", (cutoff,))
    db.commit()
    return cursor.rowcount
