"""Run-queue protocol shared by InProcessQueue and ARQQueue."""

from __future__ import annotations

import uuid
from typing import Protocol

from app.models import BoardMode


class RunQueue(Protocol):
    """Surface the API touches to start a board run asynchronously."""

    async def enqueue_run(
        self,
        run_id: uuid.UUID,
        *,
        mode_override: BoardMode | None = None,
        rounds_override: int | None = None,
    ) -> None:
        """Hand a run off to be executed.

        Returns once the job is durably accepted (in-process: scheduled on
        the loop; arq: pushed to Redis). Does NOT wait for completion.
        """
        ...

    async def close(self) -> None:
        """Release any backend resources (Redis connection pool, …)."""
        ...
