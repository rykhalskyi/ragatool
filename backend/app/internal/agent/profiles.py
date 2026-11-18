from typing import Optional

from sqlite3 import Connection

from app.crud import crud_llm_profile
from app.internal.agent.crypto import (
    ApiKeyDecryptionError,
    decrypt_api_key,
    encrypt_api_key,
)
from app.schemas.agent import (
    LlmProfileCreate,
    LlmProfileOut,
    LlmProfileUpdate,
    LlmProviderOut,
)

MASK = "••••••••"
MASK_CHAR = "•"


class ProfileNotFoundError(LookupError):
    pass


class ProfileValidationError(ValueError):
    pass


PROVIDERS: list[LlmProviderOut] = [
    LlmProviderOut(
        id="openai",
        label="OpenAI",
        default_base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
    ),
    LlmProviderOut(
        id="deepseek",
        label="DeepSeek",
        default_base_url="https://api.deepseek.com",
        default_model="deepseek-chat",
    ),
    LlmProviderOut(
        id="siliconflow",
        label="SiliconFlow",
        default_base_url="https://api.siliconflow.com/v1",
        default_model="Qwen/Qwen3-8B",
    ),
    LlmProviderOut(
        id="openrouter",
        label="OpenRouter",
        default_base_url="https://openrouter.ai/api/v1",
        default_model="openai/gpt-4o-mini",
    ),
    LlmProviderOut(
        id="custom",
        label="Custom OpenAI-compatible",
        default_base_url="",
        default_model="",
    ),
]


def list_providers() -> list[LlmProviderOut]:
    return PROVIDERS


def _mask(api_key: str) -> str:
    if len(api_key) <= 4:
        return MASK
    return MASK + api_key[-4:]


def _validate_provider(provider: str) -> str:
    provider = provider.strip()
    if provider not in {item.id for item in PROVIDERS}:
        raise ProfileValidationError(f"Unsupported provider: {provider}")
    return provider


def _require_profile(db: Connection, profile_id: str) -> dict:
    profile = crud_llm_profile.get_profile(db, profile_id)
    if profile is None:
        raise ProfileNotFoundError("LLM profile not found")
    return profile


def serialize(profile: dict) -> LlmProfileOut:
    try:
        masked = _mask(decrypt_api_key(profile["api_key"]))
    except (ApiKeyDecryptionError, RuntimeError):
        masked = MASK

    return LlmProfileOut(
        id=profile["id"],
        name=profile["name"],
        provider=profile["provider"],
        base_url=profile["base_url"],
        model=profile["model"],
        temperature=profile["temperature"],
        max_tokens=profile["max_tokens"],
        connect_timeout_seconds=profile["connect_timeout_seconds"],
        read_timeout_seconds=profile["read_timeout_seconds"],
        api_key_masked=masked,
        is_active=profile["is_active"],
        created_at=profile["created_at"],
        updated_at=profile["updated_at"],
    )


def list_profiles(db: Connection) -> list[LlmProfileOut]:
    return [serialize(profile) for profile in crud_llm_profile.list_profiles(db)]


def get_profile(db: Connection, profile_id: str) -> LlmProfileOut:
    return serialize(_require_profile(db, profile_id))


def get_raw_profile(db: Connection, profile_id: str) -> dict:
    return _require_profile(db, profile_id)


def decrypt_profile_key(profile: dict) -> str:
    try:
        return decrypt_api_key(profile["api_key"])
    except (ApiKeyDecryptionError, RuntimeError) as exc:
        raise ProfileValidationError(str(exc)) from exc


def create_profile(db: Connection, payload: LlmProfileCreate) -> LlmProfileOut:
    is_first = crud_llm_profile.count_profiles(db) == 0
    values = {
        "name": payload.name,
        "provider": _validate_provider(payload.provider),
        "base_url": payload.base_url,
        "api_key": encrypt_api_key(payload.api_key),
        "model": payload.model,
        "temperature": payload.temperature,
        "max_tokens": payload.max_tokens,
        "connect_timeout_seconds": payload.connect_timeout_seconds,
        "read_timeout_seconds": payload.read_timeout_seconds,
        "is_active": False,
    }
    created = crud_llm_profile.create_profile(db, values)
    if is_first or payload.is_active:
        crud_llm_profile.set_active(db, created["id"], True)
        created = _require_profile(db, created["id"])
    return serialize(created)


def update_profile(
    db: Connection, profile_id: str, payload: LlmProfileUpdate
) -> LlmProfileOut:
    _require_profile(db, profile_id)
    updates = {
        key: value
        for key, value in payload.model_dump(exclude_unset=True).items()
        if value is not None
    }

    if "provider" in updates:
        updates["provider"] = _validate_provider(updates["provider"])

    api_key = updates.pop("api_key", None)
    if isinstance(api_key, str):
        trimmed = api_key.strip()
        if trimmed and MASK_CHAR not in trimmed:
            updates["api_key"] = encrypt_api_key(trimmed)

    is_active = updates.pop("is_active", None)
    crud_llm_profile.update_profile(db, profile_id, updates)
    if is_active is not None:
        crud_llm_profile.set_active(db, profile_id, is_active)

    return serialize(_require_profile(db, profile_id))


def activate_profile(db: Connection, profile_id: str, active: bool) -> LlmProfileOut:
    _require_profile(db, profile_id)
    crud_llm_profile.set_active(db, profile_id, active)
    return serialize(_require_profile(db, profile_id))


def delete_profile(db: Connection, profile_id: str) -> None:
    _require_profile(db, profile_id)
    crud_llm_profile.delete_profile(db, profile_id)


def active_profile(db: Connection) -> Optional[dict]:
    for profile in crud_llm_profile.list_profiles(db):
        if profile["is_active"]:
            return profile
    return None
