from __future__ import annotations

import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError

from app.core.config import Settings, get_settings

_JWKS_TTL_SECONDS = 24 * 60 * 60
# Lower limit on how often we refresh the JWKS on a kid-miss, so a flood of
# invalid tokens cannot DoS our outbound JWKS endpoint.
_JWKS_MIN_REFRESH_INTERVAL = 60.0

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    oid: str
    username: str
    name: str | None
    roles: tuple[str, ...]
    raw_claims: dict[str, Any]


class _JwksCache:
    def __init__(self) -> None:
        self._keys: dict[str, dict[str, Any]] = {}
        self._fetched_at: float = 0.0

    async def get(self, jwks_url: str, kid: str) -> dict[str, Any] | None:
        now = time.time()
        age = now - self._fetched_at
        if not self._keys or age > _JWKS_TTL_SECONDS:
            await self._refresh(jwks_url)
            return self._keys.get(kid)
        if kid not in self._keys and age > _JWKS_MIN_REFRESH_INTERVAL:
            # Key rotation: refresh on miss, but rate-limited.
            await self._refresh(jwks_url)
        return self._keys.get(kid)

    async def _refresh(self, jwks_url: str) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(jwks_url)
            resp.raise_for_status()
            data = resp.json()
        self._keys = {k["kid"]: k for k in data.get("keys", [])}
        self._fetched_at = time.time()


_jwks_cache = _JwksCache()


async def _validate_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
        ) from exc

    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'kid' header",
        )

    key = await _jwks_cache.get(settings.jwks_url, kid)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signing key not found",
        )

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=[unverified_header.get("alg", "RS256")],
            audience=settings.azure_api_audience,
            issuer=settings.issuer,
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc

    accepted = settings.accepted_tenants
    if accepted:
        tid = claims.get("tid")
        if tid not in accepted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tenant not allowed",
            )

    return claims


def _claims_to_user(claims: dict[str, Any]) -> CurrentUser:
    oid = claims.get("oid") or claims.get("sub")
    if not oid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identifier",
        )
    return CurrentUser(
        oid=str(oid),
        username=str(claims.get("preferred_username") or claims.get("upn") or oid),
        name=claims.get("name"),
        roles=tuple(claims.get("roles", []) or []),
        raw_claims=claims,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if settings.auth_dev_bypass:
        return CurrentUser(
            oid="dev-user",
            username="dev@example.com",
            name="Local Dev User",
            roles=("admin",),
            raw_claims={},
        )

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = await _validate_token(credentials.credentials, settings)
    return _claims_to_user(claims)


def require_roles(
    *required: str,
) -> Callable[..., Coroutine[Any, Any, CurrentUser]]:
    """Dependency factory: 403 unless the caller carries at least one role."""

    async def _dep(
        user: CurrentUser = Depends(get_current_user),
        settings: Settings = Depends(get_settings),
    ) -> CurrentUser:
        if settings.auth_dev_bypass:
            return user
        expected = set(required) or set(settings.required_api_role_names)
        if not expected:
            return user
        if not expected.intersection(user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role(s): {sorted(expected)}",
            )
        return user

    return _dep
