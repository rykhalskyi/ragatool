import os
import time
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app import database

KEY_FILE_MODE = 0o600
_READ_ATTEMPTS = 50
_READ_DELAY_SECONDS = 0.02


class ApiKeyDecryptionError(RuntimeError):
    pass


def _key_file_path() -> Path:
    explicit = os.getenv("RAGATOOL_ENCRYPTION_KEY_FILE", "").strip()
    if explicit:
        return Path(explicit).expanduser()

    database_path = database.DATABASE_URL
    if database_path in {":memory:", ""} or database_path.startswith("file:"):
        return Path.cwd() / ".llm_key"
    return Path(database_path).expanduser().resolve().parent / ".llm_key"


def _restrict_permissions(path: Path) -> None:
    """Best-effort enforce 0600 on the key file."""
    try:
        if path.stat().st_mode & 0o077:
            os.chmod(path, KEY_FILE_MODE)
    except OSError:
        pass


def _read_key(path: Path) -> str:
    """Read a key, retrying briefly in case another process is still writing it."""
    for attempt in range(_READ_ATTEMPTS):
        try:
            existing = path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return ""
        if existing:
            _restrict_permissions(path)
            return existing
        if attempt < _READ_ATTEMPTS - 1:
            time.sleep(_READ_DELAY_SECONDS)
    return ""


def _load_or_create_key() -> str:
    path = _key_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = _read_key(path)
    if existing:
        return existing

    key = Fernet.generate_key().decode("utf-8")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, KEY_FILE_MODE)
    except FileExistsError:
        existing = _read_key(path)
        if existing:
            return existing
        raise RuntimeError(
            f"The LLM encryption key file at {path} exists but is empty"
        )
    except OSError as exc:
        raise RuntimeError(
            f"Could not create the LLM encryption key file at {path}"
        ) from exc

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(key)
    except Exception:
        try:
            path.unlink(missing_ok=True)
        finally:
            raise
    _restrict_permissions(path)
    return key


def get_fernet() -> Fernet:
    configured = os.getenv("RAGATOOL_ENCRYPTION_KEY", "").strip()
    key = configured or _load_or_create_key()
    try:
        return Fernet(key.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise RuntimeError(
            "RAGATOOL_ENCRYPTION_KEY must be a valid Fernet key"
        ) from exc


def encrypt_api_key(api_key: str) -> str:
    return get_fernet().encrypt(api_key.encode("utf-8")).decode("utf-8")


def decrypt_api_key(ciphertext: str) -> str:
    try:
        return get_fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ApiKeyDecryptionError(
            "The stored API key could not be decrypted. Re-enter it in Settings."
        ) from exc
