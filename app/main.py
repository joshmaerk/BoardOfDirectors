from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.v1 import api_v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import CorrelationIdMiddleware, SecurityHeadersMiddleware
from app.core.secrets import hydrate_env_from_key_vault
from app.services.llm import LLMRouter
from app.services.queue import build_queue


def _rate_limit_key(request: Request) -> str:
    """Per-user key when authenticated, falls back to client IP otherwise."""
    user = getattr(request.state, "user_oid", None)
    if user:
        return f"user:{user}"
    return get_remote_address(request)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    resolved = hydrate_env_from_key_vault(settings.azure_key_vault_url)

    # Build the RunQueue once and stash on app.state; the dep reads it back.
    llm = LLMRouter(settings)
    queue = build_queue(settings, llm)
    app.state.run_queue = queue

    get_logger(__name__).info(
        "startup",
        allowed_origins=settings.allowed_origins,
        auth_dev_bypass=settings.auth_dev_bypass,
        key_vault_secrets_resolved=resolved,
        run_queue_backend=settings.run_queue_backend,
    )
    try:
        yield
    finally:
        await queue.close()


def create_app() -> FastAPI:
    settings = get_settings()
    docs_kwargs: dict = {}
    if not settings.expose_openapi_docs:
        docs_kwargs = {"docs_url": None, "redoc_url": None, "openapi_url": None}

    limiter = Limiter(
        key_func=_rate_limit_key,
        default_limits=[settings.rate_limit_default],
    )

    app = FastAPI(
        title="Board of Directors API",
        version="0.1.0",
        lifespan=lifespan,
        **docs_kwargs,
    )
    app.state.limiter = limiter
    app.state.rate_limit_runs = settings.rate_limit_runs

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": f"Rate limit exceeded: {exc.detail}"},
        )

    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.include_router(api_v1_router)
    return app


app = create_app()
