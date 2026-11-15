import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

TOKEN_COLUMNS = "id, name, prefix, created_at, last_used_at, revoked_at"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
    return dict(row) if row is not None else None


def create_token(
    db: sqlite3.Connection, name: str, token_hash: str, prefix: str
) -> dict:
    token_id = uuid.uuid4().hex
    db.execute(
        "INSERT INTO api_tokens (id, name, token_hash, prefix) VALUES (?, ?, ?, ?)",
        (token_id, name, token_hash, prefix),
    )
    db.commit()
    row = db.execute(
        f"SELECT {TOKEN_COLUMNS} FROM api_tokens WHERE id = ?", (token_id,)
    ).fetchone()
    result = _row_to_dict(row)
    if result is None:
        raise RuntimeError("Failed to create token")
    return result


def list_tokens(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute(
        f"SELECT {TOKEN_COLUMNS} FROM api_tokens ORDER BY created_at DESC"
    ).fetchall()
    return [dict(row) for row in rows]


def find_active_by_hash(db: sqlite3.Connection, token_hash: str) -> Optional[dict]:
    row = db.execute(
        f"SELECT {TOKEN_COLUMNS} FROM api_tokens "
        "WHERE token_hash = ? AND revoked_at IS NULL",
        (token_hash,),
    ).fetchone()
    return _row_to_dict(row)


def revoke_token(db: sqlite3.Connection, token_id: str) -> bool:
    cursor = db.execute(
        "UPDATE api_tokens SET revoked_at = ? "
        "WHERE id = ? AND revoked_at IS NULL",
        (_now(), token_id),
    )
    db.commit()
    return cursor.rowcount > 0


def touch_token(
    db: sqlite3.Connection, token_id: str, min_interval_seconds: int = 60
) -> None:
    """Update last_used_at at most once per interval to avoid write churn."""
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(seconds=min_interval_seconds)).isoformat()
    db.execute(
        "UPDATE api_tokens SET last_used_at = ? "
        "WHERE id = ? AND (last_used_at IS NULL OR last_used_at <= ?)",
        (now.isoformat(), token_id, cutoff),
    )
    db.commit()
