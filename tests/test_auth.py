from __future__ import annotations

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from jose import jwt
from jose.utils import long_to_base64

from app.core.config import get_settings
from app.core.security import _jwks_cache, get_current_user

pytestmark = pytest.mark.asyncio


def _make_keypair() -> tuple[str, dict]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    nums = private_key.public_key().public_numbers()
    jwk_dict = {
        "kty": "RSA",
        "kid": "test-key-1",
        "use": "sig",
        "alg": "RS256",
        "n": long_to_base64(nums.n).decode(),
        "e": long_to_base64(nums.e).decode(),
    }
    return pem, jwk_dict


def _build_app() -> FastAPI:
    app = FastAPI()

    @app.get("/whoami")
    async def whoami(user=Depends(get_current_user)):
        return {"oid": user.oid, "username": user.username}

    return app


@pytest.fixture
def auth_settings(monkeypatch):
    monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant-123")
    monkeypatch.setenv("AZURE_API_AUDIENCE", "api://test")
    get_settings.cache_clear()
    yield get_settings()
    get_settings.cache_clear()


@pytest.fixture
def signing_keys():
    pem, jwk_dict = _make_keypair()
    _jwks_cache._keys = {jwk_dict["kid"]: jwk_dict}
    _jwks_cache._fetched_at = 9_999_999_999.0
    yield pem, jwk_dict
    _jwks_cache._keys = {}
    _jwks_cache._fetched_at = 0.0


async def _get_whoami(token: str | None) -> tuple[int, dict]:
    app = _build_app()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/whoami", headers=headers)
    return resp.status_code, resp.json()


async def test_valid_token_passes(auth_settings, signing_keys):
    pem, jwk_dict = signing_keys
    token = jwt.encode(
        {
            "iss": auth_settings.issuer,
            "aud": auth_settings.azure_api_audience,
            "tid": auth_settings.azure_tenant_id,
            "oid": "abc-123",
            "preferred_username": "alice@example.com",
            "exp": 9_999_999_999,
        },
        pem,
        algorithm="RS256",
        headers={"kid": jwk_dict["kid"]},
    )
    status_code, body = await _get_whoami(token)
    assert status_code == 200
    assert body == {"oid": "abc-123", "username": "alice@example.com"}


async def test_missing_token_rejected(auth_settings):
    status_code, _ = await _get_whoami(None)
    assert status_code == 401


async def test_wrong_audience_rejected(auth_settings, signing_keys):
    pem, jwk_dict = signing_keys
    token = jwt.encode(
        {
            "iss": auth_settings.issuer,
            "aud": "api://someone-else",
            "oid": "abc-123",
            "exp": 9_999_999_999,
        },
        pem,
        algorithm="RS256",
        headers={"kid": jwk_dict["kid"]},
    )
    status_code, _ = await _get_whoami(token)
    assert status_code == 401


async def test_unknown_kid_rejected(auth_settings, signing_keys, monkeypatch):
    pem, _ = signing_keys

    async def _noop_refresh(_url: str) -> None:
        _jwks_cache._keys = {}
        _jwks_cache._fetched_at = 9_999_999_999.0

    monkeypatch.setattr(_jwks_cache, "_refresh", _noop_refresh)
    _jwks_cache._keys = {}  # force a "miss" path without a real network call

    token = jwt.encode(
        {
            "iss": auth_settings.issuer,
            "aud": auth_settings.azure_api_audience,
            "oid": "abc-123",
            "exp": 9_999_999_999,
        },
        pem,
        algorithm="RS256",
        headers={"kid": "unknown-kid"},
    )
    status_code, _ = await _get_whoami(token)
    assert status_code == 401


async def test_dev_bypass_returns_dev_user(monkeypatch):
    monkeypatch.setenv("AUTH_DEV_BYPASS", "true")
    get_settings.cache_clear()
    try:
        status_code, body = await _get_whoami(None)
        assert status_code == 200
        assert body["oid"] == "dev-user"
    finally:
        get_settings.cache_clear()
