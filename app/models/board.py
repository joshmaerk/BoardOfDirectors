from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Visibility(enum.StrEnum):
    PRIVATE = "private"
    SHARED = "shared"


class BoardMode(enum.StrEnum):
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    DISCUSSION = "discussion"


class Board(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "boards"
    __table_args__ = (Index("ix_boards_owner_id", "owner_id"),)

    owner_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode: Mapped[BoardMode] = mapped_column(
        SAEnum(BoardMode, name="board_mode"),
        nullable=False,
        default=BoardMode.PARALLEL,
    )
    rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    synthesis_director_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(),
        ForeignKey("directors.id", ondelete="SET NULL"),
        nullable=True,
    )
    visibility: Mapped[Visibility] = mapped_column(
        SAEnum(Visibility, name="visibility", create_type=False),
        nullable=False,
        default=Visibility.PRIVATE,
    )

    members: Mapped[list[BoardDirector]] = relationship(
        back_populates="board",
        cascade="all, delete-orphan",
        order_by="BoardDirector.position",
    )


class BoardDirector(Base):
    __tablename__ = "board_directors"

    board_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("boards.id", ondelete="CASCADE"),
        primary_key=True,
    )
    director_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("directors.id", ondelete="CASCADE"),
        primary_key=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prompt_override: Mapped[str | None] = mapped_column(Text, nullable=True)

    board: Mapped[Board] = relationship(back_populates="members")
    director = relationship("Director")
