import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app import database


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


def _load_or_create_key() -> str:
    path = _key_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        existing = path.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    except FileNotFoundError:
        pass

    key = Fernet.generate_key().decode("utf-8")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return path.read_text(encoding="utf-8").strip()
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
