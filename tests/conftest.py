from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

os.environ.setdefault("AUTH_DEV_BYPASS", "true")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from app.api.v1.deps import get_llm_client
from app.core.db import get_db
from app.core.security import CurrentUser, get_current_user
from app.main import create_app
from app.models import Base
from app.services import board_runner as board_runner_module
from app.services.llm.base import ChatMessage, LLMResponse


class FakeLLMClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[ChatMessage], float]] = []

    async def chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        temperature: float,
    ) -> LLMResponse:
        self.calls.append((model, list(messages), temperature))
        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        system = next((m.content for m in messages if m.role == "system"), "")
        echo = f"[{model}] system={system[:30]} user={last_user[:60]}"
        return LLMResponse(
            content=echo,
            prompt_tokens=len(echo),
            completion_tokens=len(echo),
            latency_ms=1,
        )


@pytest_asyncio.fixture
async def engine():
    # Shared in-memory SQLite: StaticPool keeps a single connection so the
    # API request and the background runner see the same data.
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture
def fake_user() -> CurrentUser:
    return CurrentUser(
        oid="user-a",
        username="a@example.com",
        name="User A",
        roles=(),
        raw_claims={},
    )


@pytest.fixture
def other_user() -> CurrentUser:
    return CurrentUser(
        oid="user-b",
        username="b@example.com",
        name="User B",
        roles=(),
        raw_claims={},
    )


@pytest.fixture
def fake_llm() -> FakeLLMClient:
    return FakeLLMClient()


@pytest_asyncio.fixture
async def app(session_factory, fake_user, fake_llm):
    fastapi_app = create_app()

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    async def override_user() -> CurrentUser:
        return fake_user

    def override_llm() -> FakeLLMClient:
        return fake_llm

    fastapi_app.dependency_overrides[get_db] = override_db
    fastapi_app.dependency_overrides[get_current_user] = override_user
    fastapi_app.dependency_overrides[get_llm_client] = override_llm

    original_session_local = board_runner_module.SessionLocal
    board_runner_module.SessionLocal = session_factory
    try:
        yield fastapi_app
    finally:
        board_runner_module.SessionLocal = original_session_local


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


def login_as(app, user: CurrentUser) -> None:
    """Helper for tests that need to switch the authenticated user."""

    async def override_user() -> CurrentUser:
        return user

    app.dependency_overrides[get_current_user] = override_user
