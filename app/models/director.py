from __future__ import annotations

from sqlalchemy import JSON, Float, Index, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.board import Visibility


class Director(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "directors"
    __table_args__ = (Index("ix_directors_owner_id", "owner_id"),)

    owner_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(120), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    tools: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    visibility: Mapped[Visibility] = mapped_column(
        SAEnum(Visibility, name="visibility"),
        nullable=False,
        default=Visibility.PRIVATE,
    )
