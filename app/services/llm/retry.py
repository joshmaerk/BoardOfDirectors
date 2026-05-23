"""Retry / timeout / failure-classification wrapper around any LLMClient."""

from __future__ import annotations

import httpx
from openai import APIError, APIStatusError
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from app.services.llm.base import ChatMessage, LLMClient, LLMResponse


def _is_retryable(exc: BaseException) -> bool:
    """Decide whether an LLM-call failure is worth retrying.

    Retry on transient transport errors and on 429 / 5xx from any provider.
    Do not retry on 4xx client errors (bad request, auth) — those will keep
    failing the same way.
    """
    if isinstance(exc, httpx.TimeoutException | httpx.NetworkError):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code == 429 or 500 <= exc.status_code < 600
    if isinstance(exc, APIError):
        return True  # the openai SDK's general transport error
    # Azure SDK raises HttpResponseError; treat 5xx/429 as retryable.
    status = getattr(exc, "status_code", None)
    return isinstance(status, int) and (status == 429 or 500 <= status < 600)


class RetryingLLMClient:
    """Wrap another `LLMClient` with bounded retries and exponential backoff."""

    def __init__(
        self,
        inner: LLMClient,
        *,
        max_attempts: int = 3,
        backoff_initial: float = 1.0,
        backoff_max: float = 8.0,
    ) -> None:
        self._inner = inner
        self._retrying = AsyncRetrying(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=backoff_initial, max=backoff_max) + wait_random(0, 1),
            retry=retry_if_exception(_is_retryable),
            reraise=True,
        )

    async def chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        temperature: float,
    ) -> LLMResponse:
        try:
            async for attempt in self._retrying:
                with attempt:
                    return await self._inner.chat(
                        model=model, messages=messages, temperature=temperature
                    )
        except RetryError as exc:
            last = exc.last_attempt.exception()
            if last is not None:
                raise last from exc
            raise
        raise RuntimeError("RetryingLLMClient exhausted attempts without raising")
