from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.v1.deps import get_request_id, get_run_queue
from app.core.config import Settings, get_settings
from app.core.db import SessionLocal, get_db
from app.core.security import CurrentUser, get_current_user
from app.models import Board, Director, DirectorMessage, Run, RunStatus
from app.schemas.run import DirectorMessageOut, RunCreate, RunOut, RunWithMessagesOut
from app.services import audit, idempotency
from app.services.queue import RunQueue
from app.services.rate_limit import RateLimiter, get_rate_limiter

IDEMPOTENCY_HEADER = "Idempotency-Key"

router = APIRouter(tags=["runs"])


async def _get_owned_run(run_id: uuid.UUID, db: AsyncSession, user: CurrentUser) -> Run:
    run = await db.get(Run, run_id)
    if run is None or run.is_deleted or run.owner_id != user.oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


@router.get("/runs", response_model=list[RunOut])
async def list_runs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[Run]:
    result = await db.scalars(
        select(Run)
        .where(Run.owner_id == user.oid, Run.deleted_at.is_(None))
        .order_by(Run.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result)


@router.post(
    "/boards/{board_id}/runs",
    response_model=RunOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_run(
    board_id: uuid.UUID,
    payload: RunCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    queue: RunQueue = Depends(get_run_queue),
    request_id: str | None = Depends(get_request_id),
    settings: Settings = Depends(get_settings),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> Run:
    request.state.user_oid = user.oid

    # Per-user, per-route rate limit (independent of the global default).
    if settings.rate_limit_runs and not limiter.check(f"runs:{user.oid}", settings.rate_limit_runs):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {settings.rate_limit_runs}",
        )

    # Idempotency: if the client retries with the same key, return the run
    # we created the first time around. Same-user scope.
    idemp_key = idempotency.normalize(request.headers.get(IDEMPOTENCY_HEADER))
    if idemp_key:
        existing_id = await idempotency.find_run_id(db, user.oid, idemp_key)
        if existing_id is not None:
            existing = await db.get(Run, existing_id)
            if existing is not None and not existing.is_deleted:
                return existing

    board = await db.get(Board, board_id)
    if board is None or board.is_deleted or board.owner_id != user.oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")

    run = Run(
        board_id=board.id,
        owner_id=user.oid,
        input=payload.input,
        status=RunStatus.PENDING,
    )
    db.add(run)
    await db.flush()
    await audit.record(
        db,
        actor_oid=user.oid,
        action="run.started",
        resource_type="run",
        resource_id=run.id,
        request_id=request_id,
        meta={
            "board_id": str(board.id),
            "mode_override": payload.mode_override.value if payload.mode_override else None,
            "rounds_override": payload.rounds_override,
            "idempotency_key": idemp_key,
        },
    )
    if idemp_key:
        await idempotency.record(db, user.oid, idemp_key, run.id, settings.idempotency_ttl_seconds)
    await db.commit()
    await db.refresh(run)

    await queue.enqueue_run(
        run.id,
        mode_override=payload.mode_override,
        rounds_override=payload.rounds_override,
    )
    return run


@router.get("/runs/{run_id}", response_model=RunWithMessagesOut)
async def get_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> RunWithMessagesOut:
    run = await _get_owned_run(run_id, db, user)
    messages = await db.scalars(
        select(DirectorMessage)
        .where(DirectorMessage.run_id == run.id)
        .order_by(DirectorMessage.created_at)
    )
    return RunWithMessagesOut(
        **RunOut.model_validate(run).model_dump(),
        messages=[DirectorMessageOut.model_validate(m) for m in messages],
    )


@router.get("/runs/{run_id}/messages", response_model=list[DirectorMessageOut])
async def list_run_messages(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[DirectorMessage]:
    await _get_owned_run(run_id, db, user)
    result = await db.scalars(
        select(DirectorMessage)
        .where(DirectorMessage.run_id == run_id)
        .order_by(DirectorMessage.created_at)
    )
    return list(result)


@router.post("/runs/{run_id}/cancel", response_model=RunOut)
async def cancel_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    request_id: str | None = Depends(get_request_id),
) -> Run:
    run = await _get_owned_run(run_id, db, user)
    if run.status in {RunStatus.DONE, RunStatus.FAILED, RunStatus.CANCELLED}:
        return run
    run.status = RunStatus.CANCELLED
    await audit.record(
        db,
        actor_oid=user.oid,
        action="run.cancelled",
        resource_type="run",
        resource_id=run.id,
        request_id=request_id,
    )
    await db.commit()
    await db.refresh(run)
    return run


@router.get("/runs/{run_id}/stream")
async def stream_run(
    run_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
):
    # Ownership check uses its own short-lived session and is released
    # immediately — the request-scoped dependency would otherwise keep a
    # pool connection open for the full SSE lifetime.
    async with SessionLocal() as ownership_session:
        await _get_owned_run(run_id, ownership_session, user)

    async def event_source() -> AsyncIterator[dict[str, str]]:
        seen: set[uuid.UUID] = set()
        terminal = {RunStatus.DONE, RunStatus.FAILED, RunStatus.CANCELLED}
        while True:
            async with SessionLocal() as session:
                run = await session.get(Run, run_id)
                if run is None:
                    yield {"event": "error", "data": "run vanished"}
                    return
                messages = await session.scalars(
                    select(DirectorMessage)
                    .where(DirectorMessage.run_id == run_id)
                    .order_by(DirectorMessage.created_at)
                )
                for msg in messages:
                    if msg.id in seen:
                        continue
                    seen.add(msg.id)
                    director = (
                        await session.get(Director, msg.director_id) if msg.director_id else None
                    )
                    out = DirectorMessageOut.model_validate(msg).model_dump(mode="json")
                    out["persona_name"] = director.name if director else None
                    yield {"event": "message", "data": json.dumps(out)}
                if run.status in terminal:
                    yield {
                        "event": "status",
                        "data": json.dumps(RunOut.model_validate(run).model_dump(mode="json")),
                    }
                    return
            await asyncio.sleep(1.0)

    return EventSourceResponse(event_source())
