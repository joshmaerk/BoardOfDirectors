"""Phase 3c — Idempotency-Key on POST /runs and per-route runs rate limit."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models import IdempotencyKey

pytestmark = pytest.mark.asyncio


async def _create_board(client) -> tuple[str, str]:
    d = await client.post(
        "/api/v1/directors",
        json={
            "name": "D",
            "role": "R",
            "system_prompt": "p",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
        },
    )
    did = d.json()["id"]
    b = await client.post(
        "/api/v1/boards",
        json={"name": "B", "members": [{"director_id": did, "position": 0}]},
    )
    return did, b.json()["id"]


# --- Idempotency -------------------------------------------------------------


async def test_same_idempotency_key_returns_same_run(client, session_factory):
    _, bid = await _create_board(client)
    headers = {"Idempotency-Key": "key-abc-123"}

    first = await client.post(f"/api/v1/boards/{bid}/runs", json={"input": "go"}, headers=headers)
    assert first.status_code == 202
    first_run_id = first.json()["id"]

    second = await client.post(f"/api/v1/boards/{bid}/runs", json={"input": "go"}, headers=headers)
    assert second.status_code == 202
    assert second.json()["id"] == first_run_id

    async with session_factory() as session:
        rows = list(await session.scalars(select(IdempotencyKey)))
    assert len(rows) == 1
    assert rows[0].key == "key-abc-123"


async def test_different_idempotency_keys_create_different_runs(client):
    _, bid = await _create_board(client)
    a = await client.post(
        f"/api/v1/boards/{bid}/runs",
        json={"input": "go"},
        headers={"Idempotency-Key": "a"},
    )
    b = await client.post(
        f"/api/v1/boards/{bid}/runs",
        json={"input": "go"},
        headers={"Idempotency-Key": "b"},
    )
    assert a.json()["id"] != b.json()["id"]


async def test_no_idempotency_key_always_creates_a_new_run(client):
    _, bid = await _create_board(client)
    a = await client.post(f"/api/v1/boards/{bid}/runs", json={"input": "go"})
    b = await client.post(f"/api/v1/boards/{bid}/runs", json={"input": "go"})
    assert a.status_code == b.status_code == 202
    assert a.json()["id"] != b.json()["id"]


async def test_expired_idempotency_key_falls_through_to_new_run(client, session_factory):
    _, bid = await _create_board(client)
    first = await client.post(
        f"/api/v1/boards/{bid}/runs",
        json={"input": "go"},
        headers={"Idempotency-Key": "expired"},
    )
    first_run_id = first.json()["id"]

    # Backdate the stored row so it's "expired" by the time the second call
    # checks it.
    async with session_factory() as session:
        row = await session.scalar(select(IdempotencyKey).where(IdempotencyKey.key == "expired"))
        row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        await session.commit()

    second = await client.post(
        f"/api/v1/boards/{bid}/runs",
        json={"input": "go"},
        headers={"Idempotency-Key": "expired"},
    )
    # Fresh run id, but UNIQUE(owner_id, key) means we'll keep the original
    # row in the table — that's fine; the response returned a different run.
    assert second.json()["id"] != first_run_id


async def test_idempotency_scoped_per_user(client, app, other_user):
    """User B's key shouldn't collide with User A's."""
    from tests.conftest import login_as

    _, bid = await _create_board(client)
    await client.post(
        f"/api/v1/boards/{bid}/runs",
        json={"input": "go"},
        headers={"Idempotency-Key": "shared-string"},
    )

    login_as(app, other_user)
    # User B has no boards yet; create one so the call is valid.
    _, bid_b = await _create_board(client)
    resp_b = await client.post(
        f"/api/v1/boards/{bid_b}/runs",
        json={"input": "hello"},
        headers={"Idempotency-Key": "shared-string"},
    )
    # User B's call succeeds and gets its own run id (key string collides
    # with User A but the (owner, key) pair is distinct).
    assert resp_b.status_code == 202


# --- Per-route /runs rate limit ----------------------------------------------


async def test_runs_rate_limit_returns_429_after_quota(client, monkeypatch):
    # Tighten the quota for the test.
    monkeypatch.setenv("RATE_LIMIT_RUNS", "3/minute")
    get_settings.cache_clear()
    try:
        _, bid = await _create_board(client)

        statuses = []
        for _ in range(5):
            resp = await client.post(f"/api/v1/boards/{bid}/runs", json={"input": "go"})
            statuses.append(resp.status_code)

        assert statuses.count(202) == 3
        assert statuses.count(429) == 2
    finally:
        get_settings.cache_clear()
