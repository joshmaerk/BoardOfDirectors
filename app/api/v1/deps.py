from __future__ import annotations

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.services.llm import LLMRouter
from app.services.llm.base import LLMClient
from app.services.queue import RunQueue


def get_llm_client(
    settings: Settings = Depends(get_settings),
) -> LLMClient:
    return LLMRouter(settings)


def get_request_id(request: Request) -> str | None:
    """Pulls the correlation id set by CorrelationIdMiddleware, if present."""
    return getattr(request.state, "request_id", None)


def get_run_queue(request: Request) -> RunQueue:
    """The RunQueue is built once in lifespan and stashed on app.state."""
    queue: RunQueue | None = getattr(request.app.state, "run_queue", None)
    if queue is None:
        # Test setups that bypass lifespan can install a queue manually via
        # `app.dependency_overrides`. Anything reaching this line indicates
        # a config bug, not a normal runtime path.
        raise RuntimeError("RunQueue not configured on app.state")
    return queue
