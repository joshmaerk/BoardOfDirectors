from __future__ import annotations

import pytest

from tests.conftest import login_as

pytestmark = pytest.mark.asyncio


def _payload(name: str = "CFO") -> dict:
    return {
        "name": name,
        "role": "Chief Financial Officer",
        "system_prompt": "You are the CFO. Be numerical and conservative.",
        "model": "gpt-4o-mini",
        "temperature": 0.3,
    }


async def test_create_then_list_directors(client):
    create = await client.post("/api/v1/directors", json=_payload())
    assert create.status_code == 201, create.text
    director = create.json()
    assert director["name"] == "CFO"

    listing = await client.get("/api/v1/directors")
    assert listing.status_code == 200
    assert len(listing.json()) == 1


async def test_update_director(client):
    create = await client.post("/api/v1/directors", json=_payload())
    did = create.json()["id"]

    update = await client.put(
        f"/api/v1/directors/{did}", json={"temperature": 0.9}
    )
    assert update.status_code == 200
    assert update.json()["temperature"] == 0.9


async def test_delete_director(client):
    create = await client.post("/api/v1/directors", json=_payload())
    did = create.json()["id"]

    delete = await client.delete(f"/api/v1/directors/{did}")
    assert delete.status_code == 204

    get_after = await client.get(f"/api/v1/directors/{did}")
    assert get_after.status_code == 404


async def test_owner_isolation(client, app, fake_user, other_user):
    create = await client.post("/api/v1/directors", json=_payload("Private"))
    did = create.json()["id"]

    login_as(app, other_user)
    listing = await client.get("/api/v1/directors")
    assert listing.status_code == 200
    assert listing.json() == []

    forbidden = await client.put(
        f"/api/v1/directors/{did}", json={"temperature": 0.1}
    )
    assert forbidden.status_code == 404

    login_as(app, fake_user)
    mine = await client.get("/api/v1/directors")
    assert len(mine.json()) == 1


async def test_shared_director_visible_to_others(client, app, other_user):
    payload = _payload("Shared CFO") | {"visibility": "shared"}
    await client.post("/api/v1/directors", json=payload)

    login_as(app, other_user)
    listing = await client.get("/api/v1/directors")
    assert listing.status_code == 200
    assert any(d["name"] == "Shared CFO" for d in listing.json())
