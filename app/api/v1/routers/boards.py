from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.security import CurrentUser, get_current_user
from app.models import Board, BoardDirector, Director, Visibility
from app.schemas.board import BoardCreate, BoardMemberIn, BoardOut, BoardUpdate

router = APIRouter(prefix="/boards", tags=["boards"])


async def _verify_directors_accessible(
    db: AsyncSession,
    user: CurrentUser,
    director_ids: list[uuid.UUID],
) -> None:
    if not director_ids:
        return
    result = await db.scalars(select(Director).where(Director.id.in_(director_ids)))
    by_id = {d.id: d for d in result}
    for did in director_ids:
        d = by_id.get(did)
        if d is None or (d.owner_id != user.oid and d.visibility != Visibility.SHARED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Director {did} not found or not accessible",
            )


def _members_from_payload(items: list[BoardMemberIn]) -> list[BoardDirector]:
    return [
        BoardDirector(
            director_id=m.director_id,
            position=m.position,
            prompt_override=m.prompt_override,
        )
        for m in items
    ]


@router.get("", response_model=list[BoardOut])
async def list_boards(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[Board]:
    result = await db.scalars(
        select(Board).options(selectinload(Board.members)).where(Board.owner_id == user.oid)
    )
    return list(result)


@router.post("", response_model=BoardOut, status_code=status.HTTP_201_CREATED)
async def create_board(
    payload: BoardCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Board:
    director_ids = [m.director_id for m in payload.members]
    if payload.synthesis_director_id is not None:
        director_ids.append(payload.synthesis_director_id)
    await _verify_directors_accessible(db, user, director_ids)
    data = payload.model_dump(exclude={"members"})
    board = Board(owner_id=user.oid, **data)
    board.members = _members_from_payload(payload.members)
    db.add(board)
    await db.commit()
    await db.refresh(board, attribute_names=["members"])
    return board


async def _get_owned_board(
    board_id: uuid.UUID,
    db: AsyncSession,
    user: CurrentUser,
) -> Board:
    board = await db.scalar(
        select(Board).options(selectinload(Board.members)).where(Board.id == board_id)
    )
    if board is None or board.owner_id != user.oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    return board


@router.get("/{board_id}", response_model=BoardOut)
async def get_board(
    board_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Board:
    return await _get_owned_board(board_id, db, user)


@router.put("/{board_id}", response_model=BoardOut)
async def update_board(
    board_id: uuid.UUID,
    payload: BoardUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Board:
    board = await _get_owned_board(board_id, db, user)
    data = payload.model_dump(exclude_unset=True, exclude={"members"})

    # Validate any director references in the payload before mutating state.
    new_director_ids: list[uuid.UUID] = []
    if payload.members is not None:
        new_director_ids.extend(m.director_id for m in payload.members)
    if "synthesis_director_id" in data and data["synthesis_director_id"] is not None:
        new_director_ids.append(data["synthesis_director_id"])
    if new_director_ids:
        await _verify_directors_accessible(db, user, new_director_ids)

    for field, value in data.items():
        setattr(board, field, value)
    if payload.members is not None:
        board.members.clear()
        await db.flush()
        board.members = _members_from_payload(payload.members)
    await db.commit()
    await db.refresh(board, attribute_names=["members"])
    return board


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> None:
    board = await _get_owned_board(board_id, db, user)
    await db.delete(board)
    await db.commit()
