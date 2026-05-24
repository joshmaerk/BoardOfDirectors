"""ARQ worker that drains the `run_board` queue.

Run with: `arq app.workers.runner_worker.WorkerSettings`

The worker shares the same code as the API (BoardRunner + LLMRouter) but
runs in its own process / container so API replicas can restart without
losing in-flight runs.
"""

from __future__ import annotations

import uuid
from typing import Any, ClassVar

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.models import BoardMode
from app.services.board_runner import BoardRunner
from app.services.llm import LLMRouter
from app.services.queue.arq_queue import RUN_JOB_NAME, parse_redis_settings

log = get_logger(__name__)


async def run_board(
    ctx: dict[str, Any],
    run_id_str: str,
    mode_override_value: str | None,
    rounds_override: int | None,
) -> None:
    """ARQ job: execute a single board run."""
    runner: BoardRunner = ctx["runner"]
    mode_override = BoardMode(mode_override_value) if mode_override_value else None
    log.info(
        "worker_run_starting",
        run_id=run_id_str,
        mode_override=mode_override_value,
        rounds_override=rounds_override,
    )
    await runner.execute(
        uuid.UUID(run_id_str),
        mode_override=mode_override,
        rounds_override=rounds_override,
    )
    log.info("worker_run_finished", run_id=run_id_str)


async def startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    llm = LLMRouter(settings)
    ctx["runner"] = BoardRunner(llm)
    log.info("worker_started", backend="arq")


async def shutdown(ctx: dict[str, Any]) -> None:
    log.info("worker_stopping")


class WorkerSettings:
    """Picked up by `arq app.workers.runner_worker.WorkerSettings`.

    ARQ reads attributes off `settings_cls.__dict__` (see arq.worker.get_kwargs),
    so `redis_settings` must be a `RedisSettings` instance — not a method.
    `get_settings()` is `lru_cache`d, so resolving at class-definition time is
    cheap and safe.
    """

    functions: ClassVar[list] = [(RUN_JOB_NAME, run_board)]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = parse_redis_settings(get_settings().redis_url)


# ARQ inspects functions via name lookup; let it find them on the class too.
run_board.__name__ = RUN_JOB_NAME
