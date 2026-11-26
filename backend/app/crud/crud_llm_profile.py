import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional

PROFILE_COLUMNS = (
    "id, name, provider, base_url, api_key, model, temperature, max_tokens, "
    "connect_timeout_seconds, read_timeout_seconds, is_active, created_at, updated_at"
)

UPDATABLE_COLUMNS = {
    "name",
    "provider",
    "base_url",
    "api_key",
    "model",
    "temperature",
    "max_tokens",
    "connect_timeout_seconds",
    "read_timeout_seconds",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
    if row is None:
        return None
    result = dict(row)
    result["is_active"] = bool(result["is_active"])
    return result


def list_profiles(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute(
        f"SELECT {PROFILE_COLUMNS} FROM llm_profiles ORDER BY created_at ASC, id ASC"
    ).fetchall()
    return [profile for row in rows if (profile := _row_to_dict(row)) is not None]


def get_profile(db: sqlite3.Connection, profile_id: str) -> Optional[dict]:
    row = db.execute(
        f"SELECT {PROFILE_COLUMNS} FROM llm_profiles WHERE id = ?", (profile_id,)
    ).fetchone()
    return _row_to_dict(row)


def count_profiles(db: sqlite3.Connection) -> int:
    row = db.execute("SELECT COUNT(*) AS count FROM llm_profiles").fetchone()
    return int(row["count"])


def create_profile(db: sqlite3.Connection, values: dict) -> dict:
    profile_id = uuid.uuid4().hex
    now = _now()
    db.execute(
        "INSERT INTO llm_profiles ("
        "id, name, provider, base_url, api_key, model, temperature, max_tokens, "
        "connect_timeout_seconds, read_timeout_seconds, is_active, created_at, updated_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            profile_id,
            values["name"],
            values["provider"],
            values["base_url"],
            values["api_key"],
            values["model"],
            values["temperature"],
            values["max_tokens"],
            values["connect_timeout_seconds"],
            values["read_timeout_seconds"],
            1 if values.get("is_active") else 0,
            now,
            None,
        ),
    )
    db.commit()
    created = get_profile(db, profile_id)
    if created is None:
        raise RuntimeError("Failed to create the LLM profile")
    return created


def update_profile(db: sqlite3.Connection, profile_id: str, fields: dict) -> Optional[dict]:
    allowed = {key: value for key, value in fields.items() if key in UPDATABLE_COLUMNS}
    if not allowed:
        return get_profile(db, profile_id)

    assignments = ", ".join(f"{column} = ?" for column in allowed)
    db.execute(
        f"UPDATE llm_profiles SET {assignments}, updated_at = ? WHERE id = ?",
        (*allowed.values(), _now(), profile_id),
    )
    db.commit()
    return get_profile(db, profile_id)


def delete_profile(db: sqlite3.Connection, profile_id: str) -> bool:
    cursor = db.execute("DELETE FROM llm_profiles WHERE id = ?", (profile_id,))
    db.commit()
    return cursor.rowcount > 0


def set_active(db: sqlite3.Connection, profile_id: str, active: bool) -> None:
    try:
        db.execute("UPDATE llm_profiles SET is_active = 0 WHERE is_active = 1")
        if active:
            db.execute(
                "UPDATE llm_profiles SET is_active = 1, updated_at = ? WHERE id = ?",
                (_now(), profile_id),
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
