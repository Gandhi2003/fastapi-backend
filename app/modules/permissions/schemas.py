from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import ActionType, ResourceType


class PermissionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150, description="Create customers")
    description: str | None = Field(default=None, max_length=255)
    resource: ResourceType
    action: ActionType


class PermissionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=255)
    resource: ResourceType | None = None
    action: ActionType | None = None


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: int
    name: str
    description: str | None
    resource: ResourceType
    action: ActionType
    created_at: datetime
    updated_at: datetime
