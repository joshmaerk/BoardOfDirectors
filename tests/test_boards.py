from __future__ import annotations

import pytest

from tests.conftest import login_as

pytestmark = pytest.mark.asyncio


async def _create_director(client, name: str = "CFO") -> str:
    resp = await client.post(
        "/api/v1/directors",
        json={
            "name": name,
            "role": name,
            "system_prompt": f"You are {name}.",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_create_board_with_members(client):
    d1 = await _create_director(client, "CFO")
    d2 = await _create_director(client, "CTO")

    resp = await client.post(
        "/api/v1/boards",
        json={
            "name": "Exec Board",
            "mode": "parallel",
            "members": [
                {"director_id": d1, "position": 0},
                {"director_id": d2, "position": 1},
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    board = resp.json()
    assert board["name"] == "Exec Board"
    assert len(board["members"]) == 2


async def test_create_board_rejects_inaccessible_director(client, app, other_user):
    d1 = await _create_director(client, "Mine")

    login_as(app, other_user)
    resp = await client.post(
        "/api/v1/boards",
        json={
            "name": "Sneaky",
            "members": [{"director_id": d1, "position": 0}],
        },
    )
    assert resp.status_code == 400


async def test_update_board_replaces_members(client):
    d1 = await _create_director(client, "A")
    d2 = await _create_director(client, "B")
    create = await client.post(
        "/api/v1/boards",
        json={
            "name": "B",
            "members": [{"director_id": d1, "position": 0}],
        },
    )
    bid = create.json()["id"]

    update = await client.put(
        f"/api/v1/boards/{bid}",
        json={
            "members": [
                {"director_id": d2, "position": 0},
                {"director_id": d1, "position": 1},
            ]
        },
    )
    assert update.status_code == 200, update.text
    members = update.json()["members"]
    assert [m["director_id"] for m in members] == [d2, d1]


async def test_board_owner_isolation(client, app, other_user):
    d1 = await _create_director(client, "Only")
    create = await client.post(
        "/api/v1/boards",
        json={
            "name": "Private",
            "members": [{"director_id": d1, "position": 0}],
        },
    )
    bid = create.json()["id"]

    login_as(app, other_user)
    listing = await client.get("/api/v1/boards")
    assert listing.json() == []

    get_resp = await client.get(f"/api/v1/boards/{bid}")
    assert get_resp.status_code == 404
