"""DSGVO/GDPR endpoints for the calling user.

- `GET /me/export` — full data export (directors, boards, runs, messages,
  audit events). Useful for the user to inspect what we hold on them and
  for SARs (subject access requests).
- `DELETE /me` — hard-delete of all personally-attributable data. Audit
  events become anonymized (actor_oid → "deleted-user") so the trail
  survives but no longer points back to the person.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_request_id
from app.core.db import get_db
from app.core.security import CurrentUser, get_current_user
from app.models import (
    AuditEvent,
    Board,
    BoardDirector,
    Director,
    DirectorMessage,
    Run,
)
from app.services import audit

router = APIRouter(prefix="/me", tags=["account"])

DELETED_ACTOR_PLACEHOLDER = "deleted-user"


def _row_to_dict(row) -> dict[str, Any]:
    """Serialise a SQLAlchemy row to a plain dict (works for ORM objects)."""
    data: dict[str, Any] = {}
    for col in row.__table__.columns:
        value = getattr(row, col.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        else:
            value = (
                str(value)
                if value is not None
                and not isinstance(value, str | int | float | bool | list | dict)
                else value
            )
        data[col.name] = value
    return data


@router.get("/export")
async def export_my_data(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Return everything the API has stored under the caller's `oid`."""
    directors = list(await db.scalars(select(Director).where(Director.owner_id == user.oid)))
    boards = list(await db.scalars(select(Board).where(Board.owner_id == user.oid)))
    board_ids = [b.id for b in boards]
    members = (
        list(await db.scalars(select(BoardDirector).where(BoardDirector.board_id.in_(board_ids))))
        if board_ids
        else []
    )
    runs = list(await db.scalars(select(Run).where(Run.owner_id == user.oid)))
    run_ids = [r.id for r in runs]
    messages = (
        list(await db.scalars(select(DirectorMessage).where(DirectorMessage.run_id.in_(run_ids))))
        if run_ids
        else []
    )
    audit_events = list(
        await db.scalars(select(AuditEvent).where(AuditEvent.actor_oid == user.oid))
    )

    return {
        "user": {"oid": user.oid, "username": user.username, "name": user.name},
        "exported_at": datetime.now(UTC).isoformat(),
        "directors": [_row_to_dict(d) for d in directors],
        "boards": [_row_to_dict(b) for b in boards],
        "board_members": [_row_to_dict(m) for m in members],
        "runs": [_row_to_dict(r) for r in runs],
        "director_messages": [_row_to_dict(m) for m in messages],
        "audit_events": [_row_to_dict(e) for e in audit_events],
    }


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    request_id: str | None = Depends(get_request_id),
) -> None:
    """Right-to-be-forgotten: hard-delete all data owned by the caller.

    Runs and director_messages cascade from boards via FK ON DELETE CASCADE,
    so deleting Boards + Directors + Runs covers the user footprint.
    Audit events are kept but anonymised so the security trail survives.
    """
    # Record a final audit event BEFORE wiping, using the still-known oid.
    await audit.record(
        db,
        actor_oid=user.oid,
        action="account.deleted",
        resource_type="account",
        request_id=request_id,
    )
    await db.flush()

    await db.execute(delete(Run).where(Run.owner_id == user.oid))
    await db.execute(delete(Board).where(Board.owner_id == user.oid))
    await db.execute(delete(Director).where(Director.owner_id == user.oid))
    await db.execute(
        update(AuditEvent)
        .where(AuditEvent.actor_oid == user.oid)
        .values(actor_oid=DELETED_ACTOR_PLACEHOLDER)
    )
    await db.commit()
