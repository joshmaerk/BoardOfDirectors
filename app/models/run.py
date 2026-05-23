from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Run(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "runs"
    __table_args__ = (
        Index("ix_runs_owner_id", "owner_id"),
        Index("ix_runs_board_id", "board_id"),
    )

    owner_id: Mapped[str] = mapped_column(String(64), nullable=False)
    board_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[RunStatus] = mapped_column(
        SAEnum(RunStatus, name="run_status"),
        nullable=False,
        default=RunStatus.PENDING,
    )
    input: Mapped[str] = mapped_column(Text, nullable=False)
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    messages = relationship(
        "DirectorMessage",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="DirectorMessage.created_at",
    )
