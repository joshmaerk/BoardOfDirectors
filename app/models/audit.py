from __future__ import annotations

import uuid

from sqlalchemy import JSON, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AuditEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One row per mutating, security-relevant action.

    `meta` is a JSON map kept intentionally schema-less so call-sites can
    attach context (mode override, member ids, …) without a migration.
    No FK on `resource_id` so a hard-delete of the target row does not
    cascade into the audit trail.
    """

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_actor_oid", "actor_oid"),
        Index("ix_audit_events_resource_id", "resource_id"),
    )

    actor_oid: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
