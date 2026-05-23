"""Tests for the model-name-based LLM provider router."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import Settings
from app.services.llm.base import ChatMessage, LLMResponse
from app.services.llm.router import (
    PROVIDER_AZURE_ANTHROPIC,
    PROVIDER_AZURE_OPENAI,
    LLMRouter,
    UnknownProviderError,
)


def _settings(**overrides) -> Settings:
    base: dict = {
        "azure_openai_endpoint": "https://example-openai.azure.com",
        "azure_openai_api_key": "k",
        "azure_openai_deployments": {"gpt-4o-mini": "d-openai"},
        "azure_ai_foundry_endpoint": "https://example-foundry.azure.com",
        "azure_ai_foundry_api_key": "k2",
        "azure_ai_foundry_deployments": {"claude-sonnet-4-5": "d-claude"},
        "llm_provider_map": {"gpt-": "azure-openai", "claude-": "azure-anthropic"},
    }
    base.update(overrides)
    return Settings(**base)


def test_router_picks_openai_for_gpt_models():
    router = LLMRouter(_settings())
    assert router._provider_for("gpt-4o-mini") == PROVIDER_AZURE_OPENAI


def test_router_picks_anthropic_for_claude_models():
    router = LLMRouter(_settings())
    assert router._provider_for("claude-sonnet-4-5") == PROVIDER_AZURE_ANTHROPIC


def test_router_unknown_model_raises():
    router = LLMRouter(_settings())
    with pytest.raises(UnknownProviderError):
        router._provider_for("gemini-pro")


def test_router_unknown_provider_raises():
    s = _settings(llm_provider_map={"foo-": "made-up"})
    router = LLMRouter(s)
    with pytest.raises(UnknownProviderError):
        router._client_for("made-up")


def test_router_prefers_longer_prefix():
    s = _settings(
        llm_provider_map={
            "claude-": "azure-anthropic",
            "claude-haiku-": "azure-openai",  # contrived but explicit
        }
    )
    router = LLMRouter(s)
    assert router._provider_for("claude-haiku-4-5") == PROVIDER_AZURE_OPENAI
    assert router._provider_for("claude-sonnet-4-5") == PROVIDER_AZURE_ANTHROPIC


async def test_router_dispatches_chat_to_resolved_client():
    router = LLMRouter(_settings())
    fake_response = LLMResponse(
        content="routed!", prompt_tokens=1, completion_tokens=1, latency_ms=0
    )

    with (
        patch("app.services.llm.router.AzureOpenAIClient") as openai_factory,
        patch("app.services.llm.router.AzureAnthropicClient") as anthropic_factory,
    ):
        openai_factory.return_value.chat = AsyncMock(return_value=fake_response)
        anthropic_factory.return_value.chat = AsyncMock(return_value=fake_response)

        await router.chat(
            model="gpt-4o-mini",
            messages=[ChatMessage(role="user", content="hi")],
            temperature=0.0,
        )
        await router.chat(
            model="claude-sonnet-4-5",
            messages=[ChatMessage(role="user", content="hi")],
            temperature=0.0,
        )

        openai_factory.return_value.chat.assert_awaited_once()
        anthropic_factory.return_value.chat.assert_awaited_once()


async def test_router_caches_client_instances():
    router = LLMRouter(_settings())
    fake_response = LLMResponse(content="x", prompt_tokens=0, completion_tokens=0, latency_ms=0)

    with patch("app.services.llm.router.AzureOpenAIClient") as openai_factory:
        openai_factory.return_value.chat = AsyncMock(return_value=fake_response)
        await router.chat(
            model="gpt-4o-mini", messages=[ChatMessage(role="user", content="a")], temperature=0
        )
        await router.chat(
            model="gpt-4o-mini", messages=[ChatMessage(role="user", content="b")], temperature=0
        )
        assert openai_factory.call_count == 1
