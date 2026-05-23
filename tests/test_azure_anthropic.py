"""Unit tests for the Azure AI Foundry (Claude) client (mocked SDK)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.services.llm.azure_anthropic import AzureAnthropicClient
from app.services.llm.base import ChatMessage


def _settings(*, with_key: bool = True) -> Settings:
    return Settings(
        azure_ai_foundry_endpoint="https://example-foundry.services.ai.azure.com",
        azure_ai_foundry_api_key="k2" if with_key else "",
        azure_ai_foundry_deployments={"claude-sonnet-4-5": "claude-deploy"},
    )


def _fake_completion(content: str, prompt: int, completion: int):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(prompt_tokens=prompt, completion_tokens=completion),
    )


async def test_foundry_chat_resolves_deployment_and_returns_response():
    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=False)
    fake_client.complete = AsyncMock(return_value=_fake_completion("ok", 10, 5))

    with patch(
        "app.services.llm.azure_anthropic.ChatCompletionsClient",
        return_value=fake_client,
    ):
        client = AzureAnthropicClient(_settings())
        result = await client.chat(
            model="claude-sonnet-4-5",
            messages=[
                ChatMessage(role="system", content="be brief"),
                ChatMessage(role="user", content="hi"),
                ChatMessage(role="assistant", content="earlier"),
            ],
            temperature=0.4,
        )

    assert result.content == "ok"
    assert result.prompt_tokens == 10
    assert result.completion_tokens == 5

    kwargs = fake_client.complete.call_args.kwargs
    assert kwargs["model"] == "claude-deploy"
    assert kwargs["temperature"] == 0.4
    assert len(kwargs["messages"]) == 3


async def test_foundry_chat_unknown_model_raises():
    with patch(
        "app.services.llm.azure_anthropic.ChatCompletionsClient",
        return_value=MagicMock(),
    ):
        client = AzureAnthropicClient(_settings())
        with pytest.raises(ValueError, match="no Azure AI Foundry deployment"):
            await client.chat(
                model="unknown",
                messages=[ChatMessage(role="user", content="x")],
                temperature=0.0,
            )


def test_foundry_requires_endpoint():
    with pytest.raises(ValueError, match="AZURE_AI_FOUNDRY_ENDPOINT"):
        AzureAnthropicClient(Settings(azure_ai_foundry_endpoint=""))


async def test_foundry_uses_default_credential_when_no_api_key():
    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=False)
    fake_client.complete = AsyncMock(return_value=_fake_completion("x", 0, 0))

    with (
        patch(
            "app.services.llm.azure_anthropic.ChatCompletionsClient",
            return_value=fake_client,
        ) as factory,
        patch("app.services.llm.azure_anthropic.DefaultAzureCredential") as cred_factory,
    ):
        client = AzureAnthropicClient(_settings(with_key=False))
        await client.chat(
            model="claude-sonnet-4-5",
            messages=[ChatMessage(role="user", content="x")],
            temperature=0.0,
        )
        cred_factory.assert_called_once()
        # Factory was called with the DefaultAzureCredential, not an api-key creds.
        factory_kwargs = factory.call_args.kwargs
        assert "credential" in factory_kwargs
        assert "credential_scopes" in factory_kwargs
