"""Build the right RunQueue backend for the current Settings."""

from __future__ import annotations

from app.core.config import Settings
from app.services.llm.base import LLMClient
from app.services.queue.base import RunQueue
from app.services.queue.in_process import InProcessQueue


def build_queue(settings: Settings, llm: LLMClient) -> RunQueue:
    backend = (settings.run_queue_backend or "in-process").lower()
    if backend == "in-process":
        return InProcessQueue(llm)
    if backend == "arq":
        # Imported lazily so importing app.services.queue does not require
        # the arq/redis packages on environments that never enable them.
        from app.services.queue.arq_queue import ARQQueue

        return ARQQueue(settings.redis_url)
    raise ValueError(f"Unknown RUN_QUEUE_BACKEND: {backend!r}. Use 'in-process' or 'arq'.")
