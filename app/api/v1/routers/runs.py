from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.v1.deps import get_llm_client
from app.core.db import SessionLocal, get_db
from app.core.security import CurrentUser, get_current_user
from app.models import Board, DirectorMessage, Run, RunStatus
from app.schemas.run import DirectorMessageOut, RunCreate, RunOut, RunWithMessagesOut
from app.services.board_runner import BoardRunner
from app.services.llm.base import LLMClient

router = APIRouter(tags=["runs"])


async def _get_owned_run(run_id: uuid.UUID, db: AsyncSession, user: CurrentUser) -> Run:
    run = await db.get(Run, run_id)
    if run is None or run.owner_id != user.oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


@router.post(
    "/boards/{board_id}/runs",
    response_model=RunOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_run(
    board_id: uuid.UUID,
    payload: RunCreate,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    llm: LLMClient = Depends(get_llm_client),
) -> Run:
    board = await db.get(Board, board_id)
    if board is None or board.owner_id != user.oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")

    run = Run(
        board_id=board.id,
        owner_id=user.oid,
        input=payload.input,
        status=RunStatus.PENDING,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    runner = BoardRunner(llm)
    background.add_task(
        runner.execute,
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
) -> Run:
    run = await _get_owned_run(run_id, db, user)
    if run.status in {RunStatus.DONE, RunStatus.FAILED, RunStatus.CANCELLED}:
        return run
    run.status = RunStatus.CANCELLED
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
                    yield {
                        "event": "message",
                        "data": json.dumps(
                            DirectorMessageOut.model_validate(msg).model_dump(mode="json")
                        ),
                    }
                if run.status in terminal:
                    yield {
                        "event": "status",
                        "data": json.dumps(RunOut.model_validate(run).model_dump(mode="json")),
                    }
                    return
            await asyncio.sleep(1.0)

    return EventSourceResponse(event_source())
