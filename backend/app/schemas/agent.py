from typing import Any, Literal, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


def _strip_not_blank(value: str, field: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field} must not be blank")
    return value


def _validate_base_url(value: str) -> str:
    value = _strip_not_blank(value, "base_url").rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("base_url must be an http(s) URL")
    return value


class LlmProviderOut(BaseModel):
    id: str
    label: str
    default_base_url: str
    default_model: str
    requires_api_key: bool = True


class LlmProfileBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    provider: str = Field(min_length=1, max_length=64)
    base_url: str = Field(min_length=1, max_length=2048)
    model: str = Field(min_length=1, max_length=256)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=2048, ge=1, le=1_000_000)
    connect_timeout_seconds: int = Field(default=30, ge=1, le=300)
    read_timeout_seconds: int = Field(default=120, ge=1, le=600)

    @field_validator("name")
    @classmethod
    def _valid_name(cls, value: str) -> str:
        return _strip_not_blank(value, "name")

    @field_validator("provider")
    @classmethod
    def _valid_provider(cls, value: str) -> str:
        return _strip_not_blank(value, "provider")

    @field_validator("base_url")
    @classmethod
    def _valid_base_url(cls, value: str) -> str:
        return _validate_base_url(value)

    @field_validator("model")
    @classmethod
    def _valid_model(cls, value: str) -> str:
        return _strip_not_blank(value, "model")


class LlmProfileCreate(LlmProfileBase):
    api_key: str = Field(min_length=1, max_length=8192)
    is_active: bool = False

    @field_validator("api_key")
    @classmethod
    def _valid_api_key(cls, value: str) -> str:
        return _strip_not_blank(value, "api_key")


class LlmProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    provider: Optional[str] = Field(default=None, min_length=1, max_length=64)
    base_url: Optional[str] = Field(default=None, min_length=1, max_length=2048)
    api_key: Optional[str] = Field(default=None, max_length=8192)
    model: Optional[str] = Field(default=None, min_length=1, max_length=256)
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=1_000_000)
    connect_timeout_seconds: Optional[int] = Field(default=None, ge=1, le=300)
    read_timeout_seconds: Optional[int] = Field(default=None, ge=1, le=600)
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def _valid_name(cls, value: Optional[str]) -> Optional[str]:
        return None if value is None else _strip_not_blank(value, "name")

    @field_validator("provider")
    @classmethod
    def _valid_provider(cls, value: Optional[str]) -> Optional[str]:
        return None if value is None else _strip_not_blank(value, "provider")

    @field_validator("base_url")
    @classmethod
    def _valid_base_url(cls, value: Optional[str]) -> Optional[str]:
        return None if value is None else _validate_base_url(value)

    @field_validator("model")
    @classmethod
    def _valid_model(cls, value: Optional[str]) -> Optional[str]:
        return None if value is None else _strip_not_blank(value, "model")


class LlmProfileActivate(BaseModel):
    active: bool = True


class LlmProfileOut(LlmProfileBase):
    id: str
    api_key_masked: str
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None


class LlmProfileTestResult(BaseModel):
    ok: bool
    message: str
    model: Optional[str] = None
    latency_ms: Optional[int] = None


class AgentChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=20_000)

    @field_validator("content")
    @classmethod
    def _valid_content(cls, value: str) -> str:
        return _strip_not_blank(value, "content")


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    history: list[AgentChatHistoryMessage] = Field(default_factory=list, max_length=40)
    collection_name: Optional[str] = Field(default=None, max_length=512)

    @field_validator("message")
    @classmethod
    def _valid_message(cls, value: str) -> str:
        return _strip_not_blank(value, "message")

    @field_validator("collection_name")
    @classmethod
    def _valid_collection_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


class AgentToolCallOut(BaseModel):
    id: str
    name: str
    arguments: Any = None
    status: str
    result_preview: str = ""


class AgentUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class AgentChatResponse(BaseModel):
    message: str
    model: str
    tool_calls: list[AgentToolCallOut] = Field(default_factory=list)
    usage: AgentUsage = Field(default_factory=AgentUsage)
    warnings: list[str] = Field(default_factory=list)
