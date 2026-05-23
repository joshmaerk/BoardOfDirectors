from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.logging import get_logger
from app.core.security import CurrentUser, get_current_user
from app.schemas.user import UserOut

router = APIRouter(tags=["meta"])
log = get_logger(__name__)


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness probe — returns 200 unless the process is dead."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Readiness probe — fails if dependencies (DB) are not reachable."""
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        log.warning("readyz_db_unreachable", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unreachable",
        ) from exc
    return {"status": "ready"}


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser = Depends(get_current_user)) -> UserOut:
    return UserOut(
        oid=user.oid,
        username=user.username,
        name=user.name,
        roles=list(user.roles),
    )
