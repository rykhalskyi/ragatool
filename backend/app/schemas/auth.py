from typing import Optional

from pydantic import BaseModel, Field


class AuthStatus(BaseModel):
    initialized: bool


class SetupRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=256)
    setup_code: str = Field(min_length=1, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class UserOut(BaseModel):
    id: str
    username: str


class TokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class TokenOut(BaseModel):
    id: str
    name: str
    prefix: str
    created_at: Optional[str] = None
    last_used_at: Optional[str] = None
    revoked_at: Optional[str] = None


class TokenCreated(TokenOut):
    token: str
