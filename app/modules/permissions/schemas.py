"""Permission DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import ActionType, ResourceType


class PermissionCreate(BaseModel):
    # `code` is derived (resource*10 + action) by the service, not supplied here.
    name: str = Field(min_length=1, max_length=150, description="e.g. 'Create customers'")
    description: str | None = Field(default=None, max_length=255)
    resource: ResourceType  # 1=users, 2=roles, … (see ResourceType)
    action: ActionType  # 1=create, 2=read, 3=update, 4=delete


class PermissionUpdate(BaseModel):
    # All optional → PATCH semantics; only provided fields are updated.
    # Changing resource/action re-derives `code` in the service.
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=255)
    resource: ResourceType | None = None
    action: ActionType | None = None


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: int  # integer code = resource*10 + action
    name: str
    description: str | None
    resource: ResourceType
    action: ActionType
    created_at: datetime
    updated_at: datetime
