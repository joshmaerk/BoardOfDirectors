"""Per-user idempotency keys for POST /runs.

A POST that supplies the same `Idempotency-Key` header again within
`Settings.idempotency_ttl_seconds` is mapped back to the original run
instead of creating a new one. The (owner_id, key) pair is the unique
constraint — different users may reuse a key string without collision.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class IdempotencyKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("owner_id", "key", name="uq_idempotency_owner_key"),
        Index("ix_idempotency_expires_at", "expires_at"),
    )

    owner_id: Mapped[str] = mapped_column(String(64), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
