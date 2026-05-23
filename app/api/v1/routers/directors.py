from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import CurrentUser, get_current_user
from app.models import Director, Visibility
from app.schemas.director import DirectorCreate, DirectorOut, DirectorUpdate

router = APIRouter(prefix="/directors", tags=["directors"])


@router.get("", response_model=list[DirectorOut])
async def list_directors(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[Director]:
    result = await db.scalars(
        select(Director).where(
            (Director.owner_id == user.oid) | (Director.visibility == Visibility.SHARED)
        )
    )
    return list(result)


@router.post("", response_model=DirectorOut, status_code=status.HTTP_201_CREATED)
async def create_director(
    payload: DirectorCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Director:
    director = Director(owner_id=user.oid, **payload.model_dump())
    db.add(director)
    await db.commit()
    await db.refresh(director)
    return director


async def _get_owned_director(
    director_id: uuid.UUID,
    db: AsyncSession,
    user: CurrentUser,
) -> Director:
    director = await db.get(Director, director_id)
    if director is None or director.owner_id != user.oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Director not found")
    return director


@router.get("/{director_id}", response_model=DirectorOut)
async def get_director(
    director_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Director:
    director = await db.get(Director, director_id)
    if director is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Director not found")
    if director.owner_id != user.oid and director.visibility != Visibility.SHARED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Director not found")
    return director


@router.put("/{director_id}", response_model=DirectorOut)
async def update_director(
    director_id: uuid.UUID,
    payload: DirectorUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Director:
    director = await _get_owned_director(director_id, db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(director, field, value)
    await db.commit()
    await db.refresh(director)
    return director


@router.delete("/{director_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_director(
    director_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> None:
    director = await _get_owned_director(director_id, db, user)
    await db.delete(director)
    await db.commit()
