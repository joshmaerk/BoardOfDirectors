from __future__ import annotations

import time

from openai import AsyncAzureOpenAI

from app.core.config import Settings
from app.services.llm.base import ChatMessage, LLMResponse


class AzureOpenAIClient:
    def __init__(self, settings: Settings) -> None:
        self._deployments = settings.azure_openai_deployments
        self._client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )

    def _resolve_deployment(self, model: str) -> str:
        deployment = self._deployments.get(model)
        if not deployment:
            raise ValueError(
                f"Model '{model}' has no Azure OpenAI deployment mapping. "
                f"Configure AZURE_OPENAI_DEPLOYMENTS."
            )
        return deployment

    async def chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        temperature: float,
    ) -> LLMResponse:
        deployment = self._resolve_deployment(model)
        started = time.perf_counter()
        completion = await self._client.chat.completions.create(
            model=deployment,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)

        choice = completion.choices[0].message
        usage = completion.usage
        return LLMResponse(
            content=choice.content or "",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            latency_ms=latency_ms,
        )
