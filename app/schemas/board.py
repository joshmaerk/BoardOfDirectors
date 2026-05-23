from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.board import BoardMode, Visibility


class BoardMemberIn(BaseModel):
    director_id: uuid.UUID
    position: int = Field(0, ge=0)
    prompt_override: str | None = None


class BoardMemberOut(BoardMemberIn):
    model_config = ConfigDict(from_attributes=True)


class BoardBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str | None = None
    mode: BoardMode = BoardMode.PARALLEL
    rounds: int = Field(1, ge=1, le=10)
    synthesis_director_id: uuid.UUID | None = None
    visibility: Visibility = Visibility.PRIVATE


class BoardCreate(BoardBase):
    members: list[BoardMemberIn] = Field(default_factory=list)


class BoardUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = None
    mode: BoardMode | None = None
    rounds: int | None = Field(None, ge=1, le=10)
    synthesis_director_id: uuid.UUID | None = None
    visibility: Visibility | None = None
    members: list[BoardMemberIn] | None = None


class BoardOut(BoardBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: str
    created_at: datetime
    updated_at: datetime
    members: list[BoardMemberOut] = []
