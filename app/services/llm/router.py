"""Selects the right LLM client per requested model name."""

from __future__ import annotations

from app.core.config import Settings
from app.services.llm.azure_anthropic import AzureAnthropicClient
from app.services.llm.azure_openai import AzureOpenAIClient
from app.services.llm.base import ChatMessage, LLMClient, LLMResponse
from app.services.llm.retry import RetryingLLMClient

PROVIDER_AZURE_OPENAI = "azure-openai"
PROVIDER_AZURE_ANTHROPIC = "azure-anthropic"


class UnknownProviderError(ValueError):
    pass


class LLMRouter:
    """Routes `chat` calls to a provider chosen by the model-name prefix.

    Each provider client is wrapped in `RetryingLLMClient` so transient
    transport / 429 / 5xx failures are retried with exponential backoff
    before bubbling to the caller.
    """

    def __init__(self, settings: Settings, *, retries: bool = True) -> None:
        self._settings = settings
        self._provider_map = settings.llm_provider_map
        self._clients: dict[str, LLMClient] = {}
        self._retries = retries

    def _provider_for(self, model: str) -> str:
        # First match wins; ordered by descending prefix length for determinism.
        for prefix in sorted(self._provider_map, key=len, reverse=True):
            if model.startswith(prefix):
                return self._provider_map[prefix]
        raise UnknownProviderError(
            f"No provider configured for model '{model}'. Configure LLM_PROVIDER_MAP."
        )

    def _client_for(self, provider: str) -> LLMClient:
        if provider in self._clients:
            return self._clients[provider]
        if provider == PROVIDER_AZURE_OPENAI:
            client: LLMClient = AzureOpenAIClient(self._settings)
        elif provider == PROVIDER_AZURE_ANTHROPIC:
            client = AzureAnthropicClient(self._settings)
        else:
            raise UnknownProviderError(f"Provider '{provider}' is not implemented")
        if self._retries:
            client = RetryingLLMClient(client)
        self._clients[provider] = client
        return client

    async def chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        temperature: float,
    ) -> LLMResponse:
        provider = self._provider_for(model)
        client = self._client_for(provider)
        return await client.chat(model=model, messages=messages, temperature=temperature)
