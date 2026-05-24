"""Idempotency-Key lookup / claim for run creation.

Usage in the runs router:

    existing = await idempotency.find_run_id(db, user.oid, key)
    if existing is not None:
        # return the cached Run instead of creating a new one
        ...

    # ... create the Run as usual ...
    await idempotency.record(db, user.oid, key, run.id, ttl_seconds)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IdempotencyKey

# Allowed header characters: ASCII-safe, max length matches the DB column.
MAX_KEY_LENGTH = 128


def normalize(raw: str | None) -> str | None:
    if not raw:
        return None
    stripped = raw.strip()
    if not stripped or len(stripped) > MAX_KEY_LENGTH:
        return None
    return stripped


async def find_run_id(
    session: AsyncSession,
    owner_id: str,
    key: str,
) -> uuid.UUID | None:
    """Return the run id a previous request claimed for this (owner, key),
    or None if no live entry exists."""
    now = datetime.now(UTC)
    row = await session.scalar(
        select(IdempotencyKey)
        .where(IdempotencyKey.owner_id == owner_id)
        .where(IdempotencyKey.key == key)
        .where(IdempotencyKey.expires_at > now)
    )
    return row.run_id if row else None


async def record(
    session: AsyncSession,
    owner_id: str,
    key: str,
    run_id: uuid.UUID,
    ttl_seconds: int,
) -> None:
    """Claim (owner_id, key) for `run_id`. Caller owns the transaction.

    If an expired row already exists for the same (owner, key) — possible
    after TTL — it is deleted first so the INSERT succeeds. On a true
    concurrent race the caller's commit will fail with a UNIQUE violation;
    the second client should retry the GET path.
    """
    await session.execute(
        delete(IdempotencyKey)
        .where(IdempotencyKey.owner_id == owner_id)
        .where(IdempotencyKey.key == key)
    )
    session.add(
        IdempotencyKey(
            owner_id=owner_id,
            key=key,
            run_id=run_id,
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        )
    )
