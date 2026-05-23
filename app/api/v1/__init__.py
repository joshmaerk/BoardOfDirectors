from fastapi import APIRouter

from app.api.v1.routers import account, boards, directors, meta, runs

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(meta.router)
api_v1_router.include_router(account.router)
api_v1_router.include_router(directors.router)
api_v1_router.include_router(boards.router)
api_v1_router.include_router(runs.router)
