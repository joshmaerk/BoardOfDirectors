"""Phase 3a — Soft-Delete, DSGVO endpoints, Key-Vault loader, doc gating."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from sqlalchemy import select

from app.api.v1.routers.account import DELETED_ACTOR_PLACEHOLDER
from app.core.config import get_settings
from app.core.secrets import hydrate_env_from_key_vault
from app.main import create_app
from app.models import AuditEvent, Board, Director, Run

# --- Soft-delete -------------------------------------------------------------


async def _seed_director(client) -> str:
    resp = await client.post(
        "/api/v1/directors",
        json={
            "name": "D",
            "role": "R",
            "system_prompt": "p",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
        },
    )
    return resp.json()["id"]


async def test_deleted_director_excluded_from_list(client):
    did = await _seed_director(client)
    delete = await client.delete(f"/api/v1/directors/{did}")
    assert delete.status_code == 204

    listing = await client.get("/api/v1/directors")
    assert listing.json() == []


async def test_deleted_director_returns_404(client):
    did = await _seed_director(client)
    await client.delete(f"/api/v1/directors/{did}")

    get_after = await client.get(f"/api/v1/directors/{did}")
    assert get_after.status_code == 404


async def test_deleted_director_cannot_be_used_in_new_board(client):
    did = await _seed_director(client)
    await client.delete(f"/api/v1/directors/{did}")

    resp = await client.post(
        "/api/v1/boards",
        json={"name": "B", "members": [{"director_id": did, "position": 0}]},
    )
    assert resp.status_code == 400


async def test_soft_delete_keeps_row_in_db(client, session_factory):
    did = await _seed_director(client)
    await client.delete(f"/api/v1/directors/{did}")

    async with session_factory() as session:
        rows = list(await session.scalars(select(Director)))
    assert len(rows) == 1
    assert rows[0].is_deleted is True


# --- /me/export --------------------------------------------------------------


async def test_export_returns_all_owned_artifacts(client):
    did = await _seed_director(client)
    bresp = await client.post(
        "/api/v1/boards",
        json={"name": "B", "members": [{"director_id": did, "position": 0}]},
    )
    bid = bresp.json()["id"]
    await client.post(f"/api/v1/boards/{bid}/runs", json={"input": "go"})

    export = await client.get("/api/v1/me/export")
    assert export.status_code == 200
    body = export.json()
    assert body["user"]["oid"] == "user-a"
    assert len(body["directors"]) == 1
    assert len(body["boards"]) == 1
    assert len(body["runs"]) == 1
    # audit events from create-director / create-board / start-run.
    assert {e["action"] for e in body["audit_events"]} >= {
        "director.created",
        "board.created",
        "run.started",
    }


async def test_export_isolates_users(client, app, other_user):
    from tests.conftest import login_as

    await _seed_director(client)

    login_as(app, other_user)
    other_export = await client.get("/api/v1/me/export")
    assert other_export.json()["directors"] == []


# --- DELETE /me ---------------------------------------------------------------


async def test_delete_me_hard_deletes_data_and_anonymises_audit(client, session_factory):
    did = await _seed_director(client)
    bresp = await client.post(
        "/api/v1/boards",
        json={"name": "B", "members": [{"director_id": did, "position": 0}]},
    )
    bid = bresp.json()["id"]
    await client.post(f"/api/v1/boards/{bid}/runs", json={"input": "go"})

    resp = await client.delete("/api/v1/me")
    assert resp.status_code == 204

    async with session_factory() as session:
        directors = list(await session.scalars(select(Director)))
        boards = list(await session.scalars(select(Board)))
        runs = list(await session.scalars(select(Run)))
        audits = list(await session.scalars(select(AuditEvent)))
    assert directors == []
    assert boards == []
    assert runs == []
    # Audit events kept but anonymised.
    actors = {e.actor_oid for e in audits}
    assert "user-a" not in actors
    assert DELETED_ACTOR_PLACEHOLDER in actors


async def test_delete_me_only_wipes_caller_data(client, app, other_user):
    from tests.conftest import login_as

    # User A owns one director.
    await _seed_director(client)

    # User B creates their own and then deletes their account.
    login_as(app, other_user)
    other_did = await _seed_director(client)
    delete_resp = await client.delete("/api/v1/me")
    assert delete_resp.status_code == 204

    # Switch back: User A still has their director.
    from app.core.security import CurrentUser

    login_as(
        app,
        CurrentUser(
            oid="user-a",
            username="a@example.com",
            name="User A",
            roles=(),
            raw_claims={},
        ),
    )
    listing = await client.get("/api/v1/directors")
    assert len(listing.json()) == 1
    assert listing.json()[0]["id"] != other_did


# --- Key Vault loader --------------------------------------------------------


def test_kv_loader_noop_when_url_empty():
    assert hydrate_env_from_key_vault("") == 0


def test_kv_loader_resolves_marked_env_values(monkeypatch):
    monkeypatch.setenv("MY_SECRET", "@kv:db-password")
    monkeypatch.setenv("PLAIN_VAR", "not-a-secret")

    fake_secret = MagicMock()
    fake_secret.value = "s3cret"
    fake_client = MagicMock()
    fake_client.get_secret.return_value = fake_secret

    with (
        patch("azure.keyvault.secrets.SecretClient", return_value=fake_client),
        patch("azure.identity.DefaultAzureCredential"),
    ):
        count = hydrate_env_from_key_vault("https://kv.example.com")

    assert count == 1
    import os

    assert os.environ["MY_SECRET"] == "s3cret"
    assert os.environ["PLAIN_VAR"] == "not-a-secret"


def test_kv_loader_skips_on_secret_fetch_failure(monkeypatch):
    monkeypatch.setenv("MY_SECRET", "@kv:missing")
    fake_client = MagicMock()
    fake_client.get_secret.side_effect = RuntimeError("kv down")
    with (
        patch("azure.keyvault.secrets.SecretClient", return_value=fake_client),
        patch("azure.identity.DefaultAzureCredential"),
    ):
        count = hydrate_env_from_key_vault("https://kv.example.com")

    assert count == 0
    import os

    assert os.environ["MY_SECRET"] == "@kv:missing"  # untouched


# --- OpenAPI doc gating ------------------------------------------------------


def test_docs_hidden_when_gated(monkeypatch):
    monkeypatch.setenv("EXPOSE_OPENAPI_DOCS", "false")
    get_settings.cache_clear()
    try:
        gated_app = create_app()
        paths = [r.path for r in gated_app.routes]
        assert "/docs" not in paths
        assert "/openapi.json" not in paths
        assert "/redoc" not in paths
    finally:
        get_settings.cache_clear()


def test_docs_exposed_by_default(monkeypatch):
    monkeypatch.delenv("EXPOSE_OPENAPI_DOCS", raising=False)
    get_settings.cache_clear()
    try:
        default_app = create_app()
        paths = [r.path for r in default_app.routes]
        assert "/docs" in paths
        assert "/openapi.json" in paths
    finally:
        get_settings.cache_clear()
