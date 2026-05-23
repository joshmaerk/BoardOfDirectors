"""Phase 3b — run-queue abstraction and rate limiting."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.services.queue import InProcessQueue, build_queue

# --- in-process queue --------------------------------------------------------


@pytest.mark.asyncio
async def test_in_process_queue_runs_job_on_loop():
    seen: list[uuid.UUID] = []

    class FakeRunner:
        def __init__(self, *_a, **_kw):
            pass

        async def execute(self, run_id, **_kw):
            await asyncio.sleep(0)
            seen.append(run_id)

    with patch("app.services.queue.in_process.BoardRunner", FakeRunner):
        queue = InProcessQueue(llm=MagicMock())
        run_id = uuid.uuid4()
        await queue.enqueue_run(run_id)
        # Let the scheduled task run to completion before closing.
        for _ in range(10):
            if seen:
                break
            await asyncio.sleep(0)
        await queue.close()
    assert seen == [run_id]


@pytest.mark.asyncio
async def test_in_process_queue_cancels_pending_on_close():
    started = asyncio.Event()
    finished: list[bool] = []

    class HangingRunner:
        def __init__(self, *_a, **_kw):
            pass

        async def execute(self, _run_id, **_kw):
            started.set()
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                finished.append(False)
                raise

    with patch("app.services.queue.in_process.BoardRunner", HangingRunner):
        queue = InProcessQueue(llm=MagicMock())
        await queue.enqueue_run(uuid.uuid4())
        await started.wait()
        await queue.close()
    assert finished == [False]


# --- factory ----------------------------------------------------------------


def test_factory_returns_in_process_by_default():
    settings = Settings(run_queue_backend="in-process")
    queue = build_queue(settings, llm=MagicMock())
    assert isinstance(queue, InProcessQueue)


def test_factory_rejects_unknown_backend():
    settings = Settings(run_queue_backend="kafka")
    with pytest.raises(ValueError, match="Unknown RUN_QUEUE_BACKEND"):
        build_queue(settings, llm=MagicMock())


def test_factory_builds_arq_queue_lazily():
    settings = Settings(run_queue_backend="arq", redis_url="redis://localhost:6379/0")
    with patch("app.services.queue.arq_queue.ARQQueue") as ctor:
        ctor.return_value = MagicMock()
        build_queue(settings, llm=MagicMock())
    ctor.assert_called_once_with("redis://localhost:6379/0")


# --- ARQ queue (mocked redis) ------------------------------------------------


@pytest.mark.asyncio
async def test_arq_queue_enqueues_job_with_stable_id():
    from app.services.queue.arq_queue import ARQQueue

    fake_pool = MagicMock()
    fake_pool.enqueue_job = AsyncMock()
    fake_pool.aclose = AsyncMock()

    with patch("app.services.queue.arq_queue.create_pool", AsyncMock(return_value=fake_pool)):
        queue = ARQQueue("redis://example:6379/0")
        run_id = uuid.uuid4()
        await queue.enqueue_run(run_id)
        await queue.close()

    fake_pool.enqueue_job.assert_awaited_once()
    args, kwargs = fake_pool.enqueue_job.call_args
    assert args[0] == "run_board"
    assert args[1] == str(run_id)
    assert kwargs["_job_id"] == f"run:{run_id}"


# --- rate limiting -----------------------------------------------------------


async def test_rate_limit_default_returns_429_after_quota(client):
    # The default limit ("120/minute") is per-key. Burst past it.
    from app.core.config import get_settings

    settings = get_settings()
    quota_str = settings.rate_limit_default
    count, _unit = quota_str.split("/", 1)  # e.g. "120/minute"
    quota = int(count)

    # Hammer /healthz (cheap endpoint) until the bucket is empty.
    last_status = 200
    for _ in range(quota + 5):
        resp = await client.get("/api/v1/healthz")
        last_status = resp.status_code
        if last_status == 429:
            break
    assert last_status == 429, f"expected 429 within {quota + 5} calls, kept getting {last_status}"
