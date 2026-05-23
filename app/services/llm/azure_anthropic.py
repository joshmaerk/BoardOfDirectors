"""Claude on Azure AI Foundry (Models-as-a-Service) via azure-ai-inference SDK."""

from __future__ import annotations

import time

from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import (
    AssistantMessage,
    SystemMessage,
    UserMessage,
)
from azure.core.credentials import AzureKeyCredential
from azure.identity.aio import DefaultAzureCredential

from app.core.config import Settings
from app.services.llm.base import ChatMessage, LLMResponse


class AzureAnthropicClient:
    """Calls Claude models exposed as deployments on Azure AI Foundry."""

    _SCOPE = "https://cognitiveservices.azure.com/.default"

    def __init__(self, settings: Settings) -> None:
        if not settings.azure_ai_foundry_endpoint:
            raise ValueError("AZURE_AI_FOUNDRY_ENDPOINT is not configured")
        self._deployments = settings.azure_ai_foundry_deployments
        self._endpoint = settings.azure_ai_foundry_endpoint.rstrip("/")
        self._api_key = settings.azure_ai_foundry_api_key or None

    def _resolve_deployment(self, model: str) -> str:
        deployment = self._deployments.get(model)
        if not deployment:
            raise ValueError(
                f"Model '{model}' has no Azure AI Foundry deployment mapping. "
                "Configure AZURE_AI_FOUNDRY_DEPLOYMENTS."
            )
        return deployment

    def _build_client(self) -> ChatCompletionsClient:
        if self._api_key:
            return ChatCompletionsClient(
                endpoint=self._endpoint,
                credential=AzureKeyCredential(self._api_key),
            )
        # Managed Identity in Azure, az-login locally.
        return ChatCompletionsClient(
            endpoint=self._endpoint,
            credential=DefaultAzureCredential(),
            credential_scopes=[self._SCOPE],
        )

    @staticmethod
    def _convert(messages: list[ChatMessage]) -> list:
        out: list = []
        for m in messages:
            if m.role == "system":
                out.append(SystemMessage(content=m.content))
            elif m.role == "assistant":
                out.append(AssistantMessage(content=m.content))
            else:
                out.append(UserMessage(content=m.content))
        return out

    async def chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        temperature: float,
    ) -> LLMResponse:
        deployment = self._resolve_deployment(model)
        started = time.perf_counter()
        async with self._build_client() as client:
            response = await client.complete(
                model=deployment,
                messages=self._convert(messages),
                temperature=temperature,
            )
        latency_ms = int((time.perf_counter() - started) * 1000)

        choice = response.choices[0].message
        usage = getattr(response, "usage", None)
        return LLMResponse(
            content=choice.content or "",
            prompt_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
            latency_ms=latency_ms,
        )
