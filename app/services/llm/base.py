from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int


class LLMClient(Protocol):
    async def chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        temperature: float,
    ) -> LLMResponse: ...
