"""Phase 2 — input limits, observability, audit and retry tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from openai import APIStatusError
from sqlalchemy import select

from app.core.middleware import REQUEST_ID_HEADER, SECURITY_HEADERS
from app.models import AuditEvent
from app.schemas.board import MAX_BOARD_MEMBERS
from app.schemas.director import MAX_SYSTEM_PROMPT_CHARS
from app.schemas.run import MAX_RUN_INPUT_CHARS
from app.services.llm.base import ChatMessage, LLMResponse
from app.services.llm.retry import RetryingLLMClient, _is_retryable

# --- Input limits ------------------------------------------------------------


async def test_create_director_rejects_oversize_system_prompt(client):
    too_long = "x" * (MAX_SYSTEM_PROMPT_CHARS + 1)
    resp = await client.post(
        "/api/v1/directors",
        json={
            "name": "D",
            "role": "R",
            "system_prompt": too_long,
            "model": "gpt-4o-mini",
            "temperature": 0.5,
        },
    )
    assert resp.status_code == 422


async def test_create_board_rejects_too_many_members(client):
    # Create one real director, then reference its id many times.
    dresp = await client.post(
        "/api/v1/directors",
        json={
            "name": "D",
            "role": "R",
            "system_prompt": "p",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
        },
    )
    did = dresp.json()["id"]

    payload = {
        "name": "B",
        "members": [{"director_id": did, "position": i} for i in range(MAX_BOARD_MEMBERS + 1)],
    }
    resp = await client.post("/api/v1/boards", json=payload)
    assert resp.status_code == 422


async def test_run_input_size_capped(client):
    dresp = await client.post(
        "/api/v1/directors",
        json={
            "name": "D",
            "role": "R",
            "system_prompt": "p",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
        },
    )
    did = dresp.json()["id"]
    bresp = await client.post(
        "/api/v1/boards",
        json={"name": "B", "members": [{"director_id": did, "position": 0}]},
    )
    bid = bresp.json()["id"]
    resp = await client.post(
        f"/api/v1/boards/{bid}/runs",
        json={"input": "x" * (MAX_RUN_INPUT_CHARS + 1)},
    )
    assert resp.status_code == 422


# --- Observability -----------------------------------------------------------


async def test_request_id_roundtrip(client):
    resp = await client.get("/api/v1/healthz", headers={REQUEST_ID_HEADER: "trace-abc-123"})
    assert resp.headers[REQUEST_ID_HEADER] == "trace-abc-123"


async def test_request_id_generated_when_missing(client):
    resp = await client.get("/api/v1/healthz")
    rid = resp.headers.get(REQUEST_ID_HEADER)
    assert rid and len(rid) >= 32


async def test_security_headers_present(client):
    resp = await client.get("/api/v1/healthz")
    for header in SECURITY_HEADERS:
        assert header in resp.headers


async def test_readyz_passes_when_db_reachable(client):
    resp = await client.get("/api/v1/readyz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


# --- Audit trail -------------------------------------------------------------


async def test_audit_event_written_on_director_create(client, session_factory):
    resp = await client.post(
        "/api/v1/directors",
        json={
            "name": "Auditable",
            "role": "R",
            "system_prompt": "p",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
        },
    )
    assert resp.status_code == 201
    director_id = resp.json()["id"]

    async with session_factory() as session:
        events = list(await session.scalars(select(AuditEvent)))
    actions = {(e.action, str(e.resource_id)) for e in events}
    assert ("director.created", director_id) in actions


async def test_audit_event_written_on_board_create_and_run_started(client, session_factory):
    dresp = await client.post(
        "/api/v1/directors",
        json={
            "name": "D",
            "role": "R",
            "system_prompt": "p",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
        },
    )
    did = dresp.json()["id"]
    bresp = await client.post(
        "/api/v1/boards",
        json={"name": "B", "members": [{"director_id": did, "position": 0}]},
    )
    bid = bresp.json()["id"]
    rresp = await client.post(f"/api/v1/boards/{bid}/runs", json={"input": "go"})
    assert rresp.status_code == 202

    async with session_factory() as session:
        events = list(await session.scalars(select(AuditEvent)))
    actions = {e.action for e in events}
    assert {"director.created", "board.created", "run.started"} <= actions


# --- Retry wrapper -----------------------------------------------------------


def _api_status(code: int) -> APIStatusError:
    return APIStatusError("boom", response=MagicMock(status_code=code), body=None)


def test_is_retryable_classification():
    assert _is_retryable(httpx.ReadTimeout("x")) is True
    assert _is_retryable(httpx.NetworkError("x")) is True
    assert _is_retryable(_api_status(429)) is True
    assert _is_retryable(_api_status(503)) is True
    assert _is_retryable(_api_status(400)) is False
    assert _is_retryable(_api_status(401)) is False
    assert _is_retryable(ValueError("bad input")) is False


@pytest.mark.asyncio
async def test_retry_wrapper_retries_then_succeeds():
    inner = MagicMock()
    inner.chat = AsyncMock(
        side_effect=[
            _api_status(503),
            _api_status(429),
            LLMResponse(content="ok", prompt_tokens=1, completion_tokens=1, latency_ms=1),
        ]
    )
    wrapped = RetryingLLMClient(inner, max_attempts=3, backoff_initial=0.0)
    result = await wrapped.chat(
        model="m",
        messages=[ChatMessage(role="user", content="hi")],
        temperature=0.0,
    )
    assert result.content == "ok"
    assert inner.chat.await_count == 3


@pytest.mark.asyncio
async def test_retry_wrapper_does_not_retry_on_4xx():
    inner = MagicMock()
    inner.chat = AsyncMock(side_effect=_api_status(400))
    wrapped = RetryingLLMClient(inner, max_attempts=3, backoff_initial=0.0)
    with pytest.raises(APIStatusError):
        await wrapped.chat(
            model="m",
            messages=[ChatMessage(role="user", content="hi")],
            temperature=0.0,
        )
    assert inner.chat.await_count == 1


@pytest.mark.asyncio
async def test_retry_wrapper_reraises_after_max_attempts():
    inner = MagicMock()
    inner.chat = AsyncMock(side_effect=_api_status(503))
    wrapped = RetryingLLMClient(inner, max_attempts=2, backoff_initial=0.0)
    with pytest.raises(APIStatusError):
        await wrapped.chat(
            model="m",
            messages=[ChatMessage(role="user", content="hi")],
            temperature=0.0,
        )
    assert inner.chat.await_count == 2
