"""Phase 2 — auth-hardening tests."""

from __future__ import annotations

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from jose import jwt
from jose.utils import long_to_base64

from app.core.config import get_settings
from app.core.security import CurrentUser, _jwks_cache, get_current_user, require_roles


def _make_keypair() -> tuple[str, dict]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    nums = private_key.public_key().public_numbers()
    jwk = {
        "kty": "RSA",
        "kid": "k-phase-2",
        "use": "sig",
        "alg": "RS256",
        "n": long_to_base64(nums.n).decode(),
        "e": long_to_base64(nums.e).decode(),
    }
    return pem, jwk


def _build_app(roles_required: tuple[str, ...] = ()) -> FastAPI:
    app = FastAPI()
    if roles_required:
        dep = require_roles(*roles_required)

        @app.get("/admin")
        async def admin(user: CurrentUser = Depends(dep)):
            return {"oid": user.oid}

    @app.get("/whoami")
    async def whoami(user: CurrentUser = Depends(get_current_user)):
        return {"oid": user.oid, "roles": list(user.roles)}

    return app


@pytest.fixture
def auth_settings(monkeypatch):
    monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
    monkeypatch.setenv("AZURE_TENANT_ID", "primary-tenant")
    monkeypatch.setenv("AZURE_API_AUDIENCE", "api://test")
    monkeypatch.setenv("AZURE_ALLOWED_TENANTS", "primary-tenant,partner-tenant")
    get_settings.cache_clear()
    yield get_settings()
    get_settings.cache_clear()


@pytest.fixture
def signing_keys():
    pem, jwk = _make_keypair()
    _jwks_cache._keys = {jwk["kid"]: jwk}
    _jwks_cache._fetched_at = 9_999_999_999.0
    yield pem, jwk
    _jwks_cache._keys = {}
    _jwks_cache._fetched_at = 0.0


def _token(pem: str, kid: str, **overrides) -> str:
    payload = {
        "iss": "https://login.microsoftonline.com/primary-tenant/v2.0",
        "aud": "api://test",
        "tid": "primary-tenant",
        "oid": "user-1",
        "preferred_username": "u@example.com",
        "exp": 9_999_999_999,
    }
    payload.update(overrides)
    return jwt.encode(payload, pem, algorithm="RS256", headers={"kid": kid})


async def _get(app: FastAPI, path: str, token: str | None) -> tuple[int, dict]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        resp = await ac.get(path, headers=headers)
    return resp.status_code, resp.json()


async def test_token_from_unknown_tenant_rejected(auth_settings, signing_keys):
    pem, jwk = signing_keys
    token = _token(pem, jwk["kid"], tid="evil-tenant")
    status_code, body = await _get(_build_app(), "/whoami", token)
    assert status_code == 401
    assert "tenant" in body["detail"].lower()


async def test_token_from_partner_tenant_accepted(auth_settings, signing_keys):
    pem, jwk = signing_keys
    token = _token(pem, jwk["kid"], tid="partner-tenant")
    status_code, _ = await _get(_build_app(), "/whoami", token)
    assert status_code == 200


async def test_require_roles_blocks_when_role_missing(auth_settings, signing_keys):
    pem, jwk = signing_keys
    token = _token(pem, jwk["kid"])  # no roles
    app = _build_app(roles_required=("board.user",))
    status_code, body = await _get(app, "/admin", token)
    assert status_code == 403
    assert "board.user" in body["detail"]


async def test_require_roles_passes_when_role_present(auth_settings, signing_keys):
    pem, jwk = signing_keys
    token = _token(pem, jwk["kid"], roles=["board.user", "other"])
    app = _build_app(roles_required=("board.user",))
    status_code, _ = await _get(app, "/admin", token)
    assert status_code == 200


async def test_require_roles_open_when_no_roles_configured(auth_settings, signing_keys):
    pem, jwk = signing_keys
    token = _token(pem, jwk["kid"])

    async def open_dep(user: CurrentUser = Depends(require_roles())) -> dict:
        return {"oid": user.oid}

    app = FastAPI()

    @app.get("/open")
    async def open_endpoint(user: CurrentUser = Depends(require_roles())):
        return {"oid": user.oid}

    status_code, _ = await _get(app, "/open", token)
    assert status_code == 200


async def test_require_roles_under_dev_bypass(monkeypatch):
    monkeypatch.setenv("AUTH_DEV_BYPASS", "true")
    get_settings.cache_clear()
    try:
        app = FastAPI()

        @app.get("/admin")
        async def admin(user: CurrentUser = Depends(require_roles("admin"))):
            return {"oid": user.oid}

        status_code, _ = await _get(app, "/admin", None)
        assert status_code == 200
    finally:
        get_settings.cache_clear()
