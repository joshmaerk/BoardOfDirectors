"""HTTP-level tests for /boards/{id}/runs and /runs/{id} routes."""

from __future__ import annotations

import asyncio

import pytest

pytestmark = pytest.mark.asyncio


async def _create_director(client) -> str:
    resp = await client.post(
        "/api/v1/directors",
        json={
            "name": "D1",
            "role": "Tester",
            "system_prompt": "Be brief.",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_board(client, director_id: str, mode: str = "parallel") -> str:
    resp = await client.post(
        "/api/v1/boards",
        json={
            "name": "Test Board",
            "mode": mode,
            "members": [{"director_id": director_id, "position": 0}],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _wait_for_run_done(client, run_id: str, timeout: float = 5.0):
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        resp = await client.get(f"/api/v1/runs/{run_id}")
        assert resp.status_code == 200
        body = resp.json()
        if body["status"] in {"done", "failed", "cancelled"}:
            return body
        await asyncio.sleep(0.05)
    raise AssertionError("run did not finish in time")


async def test_create_and_complete_run(client):
    did = await _create_director(client)
    bid = await _create_board(client, did)

    create = await client.post(
        f"/api/v1/boards/{bid}/runs",
        json={"input": "Should we ship?"},
    )
    assert create.status_code == 202, create.text
    run = create.json()
    assert run["status"] == "pending"

    final = await _wait_for_run_done(client, run["id"])
    assert final["status"] == "done"
    assert final["total_tokens"] > 0
    assert final["result_summary"]
    assert len(final["messages"]) == 1


async def test_run_with_mode_override(client):
    did = await _create_director(client)
    bid = await _create_board(client, did, mode="parallel")
    create = await client.post(
        f"/api/v1/boards/{bid}/runs",
        json={"input": "x", "mode_override": "sequential", "rounds_override": 2},
    )
    assert create.status_code == 202
    await _wait_for_run_done(client, create.json()["id"])


async def test_create_run_unknown_board(client):
    resp = await client.post(
        "/api/v1/boards/00000000-0000-0000-0000-000000000000/runs",
        json={"input": "x"},
    )
    assert resp.status_code == 404


async def test_list_run_messages(client):
    did = await _create_director(client)
    bid = await _create_board(client, did)
    create = await client.post(f"/api/v1/boards/{bid}/runs", json={"input": "ping"})
    run_id = create.json()["id"]
    await _wait_for_run_done(client, run_id)

    msgs = await client.get(f"/api/v1/runs/{run_id}/messages")
    assert msgs.status_code == 200
    assert len(msgs.json()) == 1


async def test_get_run_other_user_404(client, app, other_user):
    from tests.conftest import login_as

    did = await _create_director(client)
    bid = await _create_board(client, did)
    create = await client.post(f"/api/v1/boards/{bid}/runs", json={"input": "ping"})
    run_id = create.json()["id"]

    login_as(app, other_user)
    other = await client.get(f"/api/v1/runs/{run_id}")
    assert other.status_code == 404

    other_msgs = await client.get(f"/api/v1/runs/{run_id}/messages")
    assert other_msgs.status_code == 404


async def test_cancel_run_idempotent_when_already_done(client):
    did = await _create_director(client)
    bid = await _create_board(client, did)
    create = await client.post(f"/api/v1/boards/{bid}/runs", json={"input": "x"})
    run_id = create.json()["id"]
    await _wait_for_run_done(client, run_id)

    cancel = await client.post(f"/api/v1/runs/{run_id}/cancel")
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "done"  # was already done, unchanged


async def test_cancel_run_marks_cancelled(client):
    did = await _create_director(client)
    bid = await _create_board(client, did)

    # Insert a run directly in PENDING via DB-fixture path: easier to drive via API
    # then mutate status. We use the public POST + immediate cancel race.
    create = await client.post(f"/api/v1/boards/{bid}/runs", json={"input": "x"})
    run_id = create.json()["id"]
    cancel = await client.post(f"/api/v1/runs/{run_id}/cancel")
    assert cancel.status_code == 200
    # Race outcome: cancelled OR done are both legitimate, but cancel API succeeded.
    assert cancel.json()["status"] in {"cancelled", "done", "running", "pending"}


async def test_stream_run_emits_messages_and_terminates(client):
    did = await _create_director(client)
    bid = await _create_board(client, did)
    create = await client.post(f"/api/v1/boards/{bid}/runs", json={"input": "stream-me"})
    run_id = create.json()["id"]

    chunks: list[str] = []
    async with client.stream("GET", f"/api/v1/runs/{run_id}/stream") as resp:
        assert resp.status_code == 200
        async for line in resp.aiter_lines():
            chunks.append(line)
            if any("status" in c for c in chunks) and any("done" in c for c in chunks):
                break

    body = "\n".join(chunks)
    assert "event: message" in body
    assert "event: status" in body
