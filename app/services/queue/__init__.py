"""Run-queue abstraction with two backends.

`InProcessQueue` runs the BoardRunner in an asyncio Task on the same event
loop as the API (good for dev / tests / single-replica deployments).

`ARQQueue` enqueues a job into Redis so a separate worker container picks it
up — restart-safe (queue survives API restarts) and horizontally scalable.

Both implementations are wired the same way from the API layer; the choice
is per-process via `Settings.run_queue_backend`.
"""

from app.services.queue.base import RunQueue
from app.services.queue.factory import build_queue
from app.services.queue.in_process import InProcessQueue

__all__ = ["InProcessQueue", "RunQueue", "build_queue"]
