"""Direct-asyncio implementation of the run queue (single-replica / dev)."""

from __future__ import annotations

import asyncio
import uuid

from app.core.logging import get_logger
from app.models import BoardMode
from app.services.board_runner import BoardRunner
from app.services.llm.base import LLMClient

log = get_logger(__name__)


class InProcessQueue:
    """Spawns the BoardRunner as an asyncio Task on the API event loop.

    Not restart-safe: jobs scheduled this way are lost if the API process
    dies before they finish. Use ARQQueue for prod.
    """

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        self._tasks: set[asyncio.Task] = set()

    async def enqueue_run(
        self,
        run_id: uuid.UUID,
        *,
        mode_override: BoardMode | None = None,
        rounds_override: int | None = None,
    ) -> None:
        runner = BoardRunner(self._llm)
        task = asyncio.create_task(
            runner.execute(
                run_id,
                mode_override=mode_override,
                rounds_override=rounds_override,
            )
        )
        # Keep a strong reference so the task isn't garbage collected mid-run.
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        log.info("run_enqueued_in_process", run_id=str(run_id))

    async def close(self) -> None:
        pending = [t for t in self._tasks if not t.done()]
        for t in pending:
            t.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
