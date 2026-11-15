from typing import Optional

from pydantic import BaseModel, Field, field_validator

BCRYPT_MAX_PASSWORD_BYTES = 72


def _strip_not_blank(value: str, field: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field} must not be blank")
    return value


def _check_bcrypt_length(password: str) -> str:
    if len(password.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError("password must be at most 72 bytes")
    return password


class AuthStatus(BaseModel):
    initialized: bool


class SetupRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=256)
    setup_code: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def _valid_username(cls, value: str) -> str:
        return _strip_not_blank(value, "username")

    @field_validator("password")
    @classmethod
    def _valid_password(cls, value: str) -> str:
        return _check_bcrypt_length(value)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("username")
    @classmethod
    def _valid_username(cls, value: str) -> str:
        return _strip_not_blank(value, "username")


class UserOut(BaseModel):
    id: str
    username: str


class TokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def _valid_name(cls, value: str) -> str:
        return _strip_not_blank(value, "name")


class TokenOut(BaseModel):
    id: str
    name: str
    prefix: str
    created_at: Optional[str] = None
    last_used_at: Optional[str] = None
    revoked_at: Optional[str] = None


class TokenCreated(TokenOut):
    token: str
