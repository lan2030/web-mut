"""Pydantic request/response schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# --- Auth ------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class PermissionOut(BaseModel):
    key: str
    description: str
    model_config = ConfigDict(from_attributes=True)


class RoleOut(BaseModel):
    id: int
    key: str
    name: str
    description: str
    is_system: bool
    permissions: list[str] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class ModuleOut(BaseModel):
    key: str
    name: str
    icon: str
    route: str
    permission: str


class MeOut(BaseModel):
    id: int
    username: str
    full_name: str
    roles: list[str]
    permissions: list[str]
    modules: list[ModuleOut]
    csrf_token: str


# --- Admin: users ----------------------------------------------------------
class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    is_active: bool
    created_at: datetime
    roles: list[str] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    full_name: str = ""
    role_ids: list[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    full_name: str | None = None
    is_active: bool | None = None
    role_ids: list[int] | None = None


class PasswordReset(BaseModel):
    password: str = Field(min_length=6, max_length=128)


# --- Admin: roles ----------------------------------------------------------
class RoleCreate(BaseModel):
    key: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    permissions: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None
