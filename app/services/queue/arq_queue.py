"""ARQ (Redis) implementation of the run queue."""

from __future__ import annotations

import uuid

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.logging import get_logger
from app.models import BoardMode

log = get_logger(__name__)

RUN_JOB_NAME = "run_board"


def parse_redis_settings(redis_url: str) -> RedisSettings:
    """`redis://[:password@]host:port/db` -> ARQ RedisSettings."""
    return RedisSettings.from_dsn(redis_url)


class ARQQueue:
    """Pushes a `run_board` job onto Redis. A separate worker container
    (see `app.workers.runner_worker`) consumes them. Restart-safe."""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._pool: ArqRedis | None = None

    async def _connect(self) -> ArqRedis:
        if self._pool is None:
            self._pool = await create_pool(parse_redis_settings(self._redis_url))
        return self._pool

    async def enqueue_run(
        self,
        run_id: uuid.UUID,
        *,
        mode_override: BoardMode | None = None,
        rounds_override: int | None = None,
    ) -> None:
        pool = await self._connect()
        # job_id makes the enqueue idempotent: a retry with the same run_id
        # is a no-op if the job already exists in the queue / in flight.
        await pool.enqueue_job(
            RUN_JOB_NAME,
            str(run_id),
            mode_override.value if mode_override else None,
            rounds_override,
            _job_id=f"run:{run_id}",
        )
        log.info("run_enqueued_arq", run_id=str(run_id))

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.aclose()
            self._pool = None
