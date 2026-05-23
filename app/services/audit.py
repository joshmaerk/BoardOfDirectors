"""Thin write API for the audit-event trail."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent


async def record(
    session: AsyncSession,
    *,
    actor_oid: str,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    request_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> AuditEvent:
    """Append an audit event. Caller owns the surrounding transaction."""
    event = AuditEvent(
        actor_oid=actor_oid,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        request_id=request_id,
        meta=meta,
    )
    session.add(event)
    return event
