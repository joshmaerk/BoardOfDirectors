"""Unit tests for the LLM provider clients (mocked SDKs)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.services.llm.azure_openai import AzureOpenAIClient
from app.services.llm.base import ChatMessage

pytestmark = pytest.mark.asyncio


def _fake_settings() -> Settings:
    return Settings(
        azure_openai_endpoint="https://example-openai.azure.com",
        azure_openai_api_key="dummy",
        azure_openai_api_version="2024-10-21",
        azure_openai_deployments={"gpt-4o-mini": "my-deployment"},
    )


async def test_azure_openai_resolves_deployment_and_returns_response():
    settings = _fake_settings()

    fake_response = SimpleNamespace(
        choices=[
            SimpleNamespace(message=SimpleNamespace(content="hello world")),
        ],
        usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7),
    )

    fake_client = MagicMock()
    fake_client.chat.completions.create = AsyncMock(return_value=fake_response)

    with patch(
        "app.services.llm.azure_openai.AsyncAzureOpenAI",
        return_value=fake_client,
    ):
        client = AzureOpenAIClient(settings)
        result = await client.chat(
            model="gpt-4o-mini",
            messages=[
                ChatMessage(role="system", content="be brief"),
                ChatMessage(role="user", content="hi"),
            ],
            temperature=0.2,
        )

    assert result.content == "hello world"
    assert result.prompt_tokens == 11
    assert result.completion_tokens == 7
    assert result.latency_ms >= 0

    create_kwargs = fake_client.chat.completions.create.call_args.kwargs
    assert create_kwargs["model"] == "my-deployment"
    assert create_kwargs["temperature"] == 0.2
    assert [m["role"] for m in create_kwargs["messages"]] == ["system", "user"]


async def test_azure_openai_unknown_model_raises():
    settings = _fake_settings()
    with patch("app.services.llm.azure_openai.AsyncAzureOpenAI", return_value=MagicMock()):
        client = AzureOpenAIClient(settings)
        with pytest.raises(ValueError, match="no Azure OpenAI deployment"):
            await client.chat(
                model="unknown-model",
                messages=[ChatMessage(role="user", content="x")],
                temperature=0.0,
            )


async def test_azure_openai_handles_missing_usage():
    settings = _fake_settings()
    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=None))],
        usage=None,
    )
    fake_client = MagicMock()
    fake_client.chat.completions.create = AsyncMock(return_value=fake_response)

    with patch(
        "app.services.llm.azure_openai.AsyncAzureOpenAI",
        return_value=fake_client,
    ):
        client = AzureOpenAIClient(settings)
        result = await client.chat(
            model="gpt-4o-mini",
            messages=[ChatMessage(role="user", content="x")],
            temperature=0.0,
        )
    assert result.content == ""
    assert result.prompt_tokens == 0
    assert result.completion_tokens == 0
