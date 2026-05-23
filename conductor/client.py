"""Wrapper around AsyncAnthropic with cumulative token tracking and budget enforcement."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import TextBlock, ToolUseBlock

from .rag import TOOL_SCHEMA as RAG_TOOL_SCHEMA
from .rag import RagTool


class BudgetExceededError(RuntimeError):
    """Raised when the cumulative output-token budget for a session is exhausted."""


@dataclass
class TokenLedger:
    budget_total: int = 80_000
    input: int = 0
    output: int = 0

    def add(self, in_tokens: int, out_tokens: int) -> None:
        self.input += in_tokens
        self.output += out_tokens

    @property
    def utilization(self) -> float:
        if not self.budget_total:
            return 0.0
        return self.output / self.budget_total

    @property
    def status(self) -> str:
        u = self.utilization
        if u < 0.7:
            return "grün"
        if u < 0.9:
            return "gelb"
        return "rot"

    def check(self) -> None:
        if self.output >= self.budget_total:
            raise BudgetExceededError(
                f"Output token budget exceeded: {self.output}/{self.budget_total}"
            )


@dataclass
class ConverseResult:
    text: str
    used_paths: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = ""


@dataclass
class ClaudeClient:
    """Async wrapper around the Anthropic Messages API.

    `converse` runs a streaming message loop that handles `tool_use` rounds for
    the Obsidian RAG tool. Each text delta is forwarded to the optional
    `on_text` callback so the caller can stream to a UI.
    """

    model: str
    ledger: TokenLedger
    api_key: str | None = None
    _client: AsyncAnthropic = field(init=False, repr=False)

    def __post_init__(self) -> None:
        key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = AsyncAnthropic(api_key=key)

    async def converse(
        self,
        *,
        system: str,
        user_message: str,
        max_tokens: int,
        rag: RagTool | None = None,
        on_text: Callable[[str], None] | None = None,
    ) -> ConverseResult:
        self.ledger.check()
        tools = [RAG_TOOL_SCHEMA] if rag is not None else None
        messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
        aggregate_text = ""
        used_paths: list[str] = []
        total_in = 0
        total_out = 0
        stop_reason = ""

        while True:
            self.ledger.check()
            kwargs: dict[str, Any] = {
                "model": self.model,
                "system": system,
                "messages": messages,
                "max_tokens": max_tokens,
            }
            if tools:
                kwargs["tools"] = tools

            text_parts: list[str] = []
            async with self._client.messages.stream(**kwargs) as stream:
                async for event in stream:
                    etype = getattr(event, "type", None)
                    if etype != "content_block_delta":
                        continue
                    delta = getattr(event, "delta", None)
                    if delta is None or getattr(delta, "type", None) != "text_delta":
                        continue
                    chunk = delta.text
                    text_parts.append(chunk)
                    if on_text:
                        on_text(chunk)
                final = await stream.get_final_message()

            aggregate_text += "".join(text_parts)
            total_in += final.usage.input_tokens
            total_out += final.usage.output_tokens
            self.ledger.add(final.usage.input_tokens, final.usage.output_tokens)
            stop_reason = final.stop_reason or ""

            tool_uses: list[ToolUseBlock] = [
                b for b in final.content if isinstance(b, ToolUseBlock)
            ]
            if stop_reason != "tool_use" or not tool_uses or rag is None:
                break

            assistant_content: list[dict[str, Any]] = []
            for block in final.content:
                if isinstance(block, TextBlock):
                    assistant_content.append({"type": "text", "text": block.text})
                elif isinstance(block, ToolUseBlock):
                    assistant_content.append(
                        {
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        }
                    )
            messages.append({"role": "assistant", "content": assistant_content})

            tool_results: list[dict[str, Any]] = []
            for tu in tool_uses:
                if tu.name == "read_obsidian_note":
                    tu_input = tu.input if isinstance(tu.input, dict) else {}
                    rel_path = str(tu_input.get("relative_path", ""))
                    content = rag.read(rel_path)
                    if rag.is_allowed(rel_path):
                        used_paths.append(rel_path)
                else:
                    content = f"[unknown tool: {tu.name}]"
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tu.id,
                        "content": content,
                    }
                )
            messages.append({"role": "user", "content": tool_results})

        return ConverseResult(
            text=aggregate_text,
            used_paths=used_paths,
            input_tokens=total_in,
            output_tokens=total_out,
            stop_reason=stop_reason,
        )
