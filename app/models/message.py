from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MessageRole(enum.StrEnum):
    DIRECTOR = "director"
    SYNTHESIS = "synthesis"


class DirectorMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "director_messages"
    __table_args__ = (Index("ix_director_messages_run_id", "run_id"),)

    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    director_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(),
        ForeignKey("directors.id", ondelete="SET NULL"),
        nullable=True,
    )
    round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    role: Mapped[MessageRole] = mapped_column(
        SAEnum(MessageRole, name="message_role"),
        nullable=False,
        default=MessageRole.DIRECTOR,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    run = relationship("Run", back_populates="messages")
