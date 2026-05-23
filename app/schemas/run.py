from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.board import BoardMode
from app.models.message import MessageRole
from app.models.run import RunStatus


class RunCreate(BaseModel):
    input: str = Field(..., min_length=1)
    mode_override: BoardMode | None = None
    rounds_override: int | None = Field(None, ge=1, le=10)


class DirectorMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    director_id: uuid.UUID | None
    round: int
    role: MessageRole
    content: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    created_at: datetime


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    board_id: uuid.UUID
    owner_id: str
    status: RunStatus
    input: str
    result_summary: str | None
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None
    total_tokens: int
    cost_usd: float
    created_at: datetime
    updated_at: datetime


class RunWithMessagesOut(RunOut):
    messages: list[DirectorMessageOut] = []
