from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_healthz(client):
    resp = await client.get("/api/v1/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_me_returns_authenticated_user(client, fake_user):
    resp = await client.get("/api/v1/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["oid"] == fake_user.oid
    assert body["username"] == fake_user.username
