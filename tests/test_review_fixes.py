"""Regression tests for the four review comments raised on PR #6.

Each test name maps to the corresponding finding.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import select

from app.models import Board, BoardMode, Director, Run, RunStatus, Visibility
from app.services import board_runner as board_runner_module
from app.services.board_runner import BoardRunner
from tests.conftest import login_as

pytestmark = pytest.mark.asyncio


async def _create_director(client, name: str = "Owned") -> str:
    resp = await client.post(
        "/api/v1/directors",
        json={
            "name": name,
            "role": name,
            "system_prompt": f"You are {name}.",
            "model": "gpt-4o-mini",
            "temperature": 0.3,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_board_with_member(client, director_id: str, mode: str = "parallel") -> str:
    resp = await client.post(
        "/api/v1/boards",
        json={
            "name": "B",
            "mode": mode,
            "rounds": 1,
            "members": [{"director_id": director_id, "position": 0}],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# --- P1: run overrides must not mutate the board row -------------------------


async def test_run_mode_override_does_not_mutate_board(client):
    did = await _create_director(client)
    bid = await _create_board_with_member(client, did, mode="parallel")

    create = await client.post(
        f"/api/v1/boards/{bid}/runs",
        json={"input": "x", "mode_override": "sequential", "rounds_override": 4},
    )
    assert create.status_code == 202

    # Wait briefly so the background runner had a chance to run.
    deadline = asyncio.get_running_loop().time() + 3.0
    while asyncio.get_running_loop().time() < deadline:
        rid = create.json()["id"]
        cur = await client.get(f"/api/v1/runs/{rid}")
        if cur.json()["status"] in {"done", "failed", "cancelled"}:
            break
        await asyncio.sleep(0.05)

    board_after = await client.get(f"/api/v1/boards/{bid}")
    assert board_after.status_code == 200
    body = board_after.json()
    assert body["mode"] == "parallel"  # unchanged
    assert body["rounds"] == 1  # unchanged


# --- P1: cancel before execute() must short-circuit --------------------------


async def test_runner_skips_execution_when_cancelled_before_start(session_factory, fake_llm):
    """Seed a Run already in CANCELLED state, run the engine, assert no LLM calls."""
    original_sl = board_runner_module.SessionLocal
    board_runner_module.SessionLocal = session_factory
    try:
        async with session_factory() as session:
            director = Director(
                owner_id="user-a",
                name="D",
                role="D",
                system_prompt="p",
                model="gpt-4o-mini",
                temperature=0.3,
                visibility=Visibility.PRIVATE,
            )
            session.add(director)
            await session.flush()

            board = Board(
                owner_id="user-a",
                name="B",
                mode=BoardMode.PARALLEL,
                rounds=1,
                visibility=Visibility.PRIVATE,
            )
            from app.models import BoardDirector

            board.members = [BoardDirector(director_id=director.id, position=0)]
            session.add(board)
            await session.flush()

            run = Run(
                owner_id="user-a",
                board_id=board.id,
                input="should not run",
                status=RunStatus.CANCELLED,  # pre-cancelled
            )
            session.add(run)
            await session.commit()
            run_id = run.id

        await BoardRunner(fake_llm).execute(run_id)

        assert fake_llm.calls == []

        async with session_factory() as session:
            fresh = await session.get(Run, run_id)
            assert fresh.status == RunStatus.CANCELLED
            assert fresh.finished_at is not None
    finally:
        board_runner_module.SessionLocal = original_sl


async def test_runner_respects_mid_run_cancel(session_factory, fake_llm):
    """Cancel a run that has just finished its director phase via DB write,
    then run synthesis — should bail out and leave status CANCELLED."""
    original_sl = board_runner_module.SessionLocal
    board_runner_module.SessionLocal = session_factory
    try:
        from app.models import BoardDirector

        async with session_factory() as session:
            director = Director(
                owner_id="user-a",
                name="D",
                role="D",
                system_prompt="p",
                model="gpt-4o-mini",
                temperature=0.3,
                visibility=Visibility.PRIVATE,
            )
            chair = Director(
                owner_id="user-a",
                name="Chair",
                role="Chair",
                system_prompt="p",
                model="gpt-4o-mini",
                temperature=0.3,
                visibility=Visibility.PRIVATE,
            )
            session.add_all([director, chair])
            await session.flush()

            board = Board(
                owner_id="user-a",
                name="B",
                mode=BoardMode.PARALLEL,
                rounds=1,
                synthesis_director_id=chair.id,
                visibility=Visibility.PRIVATE,
            )
            board.members = [BoardDirector(director_id=director.id, position=0)]
            session.add(board)
            await session.flush()

            run = Run(
                owner_id="user-a",
                board_id=board.id,
                input="x",
                status=RunStatus.PENDING,
            )
            session.add(run)
            await session.commit()
            run_id = run.id

        # Wrap the LLM so the *first* director call flips the run to CANCELLED
        # in a parallel session — simulating the cancel endpoint firing while
        # the runner is mid-execute.
        class FlipOnCallLLM:
            def __init__(self, factory):
                self.factory = factory
                self.calls = 0

            async def chat(self, **kw):
                self.calls += 1
                if self.calls == 1:
                    async with self.factory() as s:
                        r = await s.get(Run, run_id)
                        r.status = RunStatus.CANCELLED
                        await s.commit()
                return await fake_llm.chat(**kw)

        await BoardRunner(FlipOnCallLLM(session_factory)).execute(run_id)

        async with session_factory() as session:
            fresh = await session.get(Run, run_id)
            assert fresh.status == RunStatus.CANCELLED
            # Director ran once, but synthesis (chair) was skipped.
            msgs = await session.scalars(
                select(__import__("app.models", fromlist=["DirectorMessage"]).DirectorMessage)
            )
            roles = [m.role for m in msgs]
            from app.models import MessageRole

            assert MessageRole.SYNTHESIS not in roles
    finally:
        board_runner_module.SessionLocal = original_sl


# --- P1: synthesis_director_id ownership check --------------------------------


async def test_create_board_rejects_inaccessible_synthesis_director(client, app, other_user):
    # User A creates a private director.
    private_did = await _create_director(client, "A-Private")

    # User B tries to use it as synthesis chair on their board.
    login_as(app, other_user)
    own_did = await _create_director(client, "B-Own")
    resp = await client.post(
        "/api/v1/boards",
        json={
            "name": "B",
            "members": [{"director_id": own_did, "position": 0}],
            "synthesis_director_id": private_did,
        },
    )
    assert resp.status_code == 400


async def test_update_board_rejects_inaccessible_synthesis_director(client, app, other_user):
    private_did = await _create_director(client, "A-Private")

    login_as(app, other_user)
    own_did = await _create_director(client, "B-Own")
    create = await client.post(
        "/api/v1/boards",
        json={"name": "B", "members": [{"director_id": own_did, "position": 0}]},
    )
    bid = create.json()["id"]

    update = await client.put(
        f"/api/v1/boards/{bid}",
        json={"synthesis_director_id": private_did},
    )
    assert update.status_code == 400


# --- P2: stream endpoint releases its initial DB session ----------------------


async def test_stream_endpoint_does_not_keep_request_session(client):
    """Smoke test: the stream endpoint still works and terminates cleanly after
    removing the request-scoped DB dependency."""
    did = await _create_director(client)
    bid = await _create_board_with_member(client, did)
    create = await client.post(f"/api/v1/boards/{bid}/runs", json={"input": "ping"})
    run_id = create.json()["id"]

    lines: list[str] = []
    async with client.stream("GET", f"/api/v1/runs/{run_id}/stream") as resp:
        assert resp.status_code == 200
        async for line in resp.aiter_lines():
            lines.append(line)
            if any("event: status" in item for item in lines):
                break

    assert any("event: message" in item for item in lines)


async def test_stream_endpoint_404s_for_unknown_run(client):
    unknown = uuid.uuid4()
    async with client.stream("GET", f"/api/v1/runs/{unknown}/stream") as resp:
        assert resp.status_code == 404
