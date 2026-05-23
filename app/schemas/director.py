from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.board import Visibility

MAX_SYSTEM_PROMPT_CHARS = 16_000


class DirectorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    role: str = Field(..., min_length=1, max_length=120)
    system_prompt: str = Field(..., min_length=1, max_length=MAX_SYSTEM_PROMPT_CHARS)
    model: str = Field(..., min_length=1, max_length=64)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    tools: dict[str, Any] | None = None
    visibility: Visibility = Visibility.PRIVATE


class DirectorCreate(DirectorBase):
    pass


class DirectorUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    role: str | None = Field(None, min_length=1, max_length=120)
    system_prompt: str | None = Field(None, min_length=1, max_length=MAX_SYSTEM_PROMPT_CHARS)
    model: str | None = Field(None, min_length=1, max_length=64)
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    tools: dict[str, Any] | None = None
    visibility: Visibility | None = None


class DirectorOut(DirectorBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: str
    created_at: datetime
    updated_at: datetime
