"""Tests for the DebateEngine using a fake Claude client."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import pytest

from conductor.client import BudgetExceededError, ConverseResult, TokenLedger
from conductor.config import Config
from conductor.debate_engine import (
    CONVERGENCE_PROMPT,
    DEVILS_REACTION_PROMPT,
    DebateEngine,
    _parse_convergence_json,
)
from conductor.personas import PersonaRegistry

AGENTS_DIR = Path(__file__).resolve().parents[1] / ".claude" / "agents"


@dataclass
class RecordedCall:
    system: str
    user_message: str
    max_tokens: int


@dataclass
class FakeClient:
    ledger: TokenLedger
    text_for: Callable[[RecordedCall, int], str] = field(default=lambda call, i: "OK")
    calls: list[RecordedCall] = field(default_factory=list)
    fail_after: Optional[int] = None
    fixed_in_tokens: int = 10
    fixed_out_tokens: int = 20

    async def converse(
        self,
        *,
        system: str,
        user_message: str,
        max_tokens: int,
        rag=None,
        on_text=None,
    ) -> ConverseResult:
        self.ledger.check()
        call = RecordedCall(system=system, user_message=user_message, max_tokens=max_tokens)
        self.calls.append(call)
        idx = len(self.calls) - 1
        if self.fail_after is not None and idx >= self.fail_after:
            self.ledger.add(0, self.ledger.budget_total)
            raise BudgetExceededError("forced abort")
        text = self.text_for(call, idx)
        if on_text:
            on_text(text)
        self.ledger.add(self.fixed_in_tokens, self.fixed_out_tokens)
        return ConverseResult(
            text=text,
            used_paths=[],
            input_tokens=self.fixed_in_tokens,
            output_tokens=self.fixed_out_tokens,
            stop_reason="end_turn",
        )


def _config() -> Config:
    cfg = Config()
    cfg.debate.token_budget_total = 1_000_000
    cfg.debate.convergence_detection = False
    return cfg


def _personas() -> PersonaRegistry:
    return PersonaRegistry.load_all(AGENTS_DIR)


def test_run_executes_all_four_rounds_and_records_contributions():
    cfg = _config()
    personas = _personas()
    ledger = TokenLedger(budget_total=cfg.debate.token_budget_total)

    def text_for(call: RecordedCall, idx: int) -> str:
        if "SCQA-Briefing" in call.user_message:
            return "## Situation\nS\n\n## Complication\nC\n\n## Question\nQ\n\n## Answer\n- a\n- b\n- c\n\n## Empfehlung\nE"
        return f"text-{idx}"

    fake = FakeClient(ledger=ledger, text_for=text_for)
    engine = DebateEngine(config=cfg, client=fake, personas=personas)
    state = asyncio.run(engine.run("Testfrage"))

    # 5 personas across rounds 1+2+3 = 15 + 1 moderator open + 1 synthesis = 17 calls
    assert len(fake.calls) == 17
    assert len(state.round(1)) == 5
    assert len(state.round(2)) == 5
    assert len(state.round(3)) == 5
    assert state.moderator_opening
    assert "## Situation" in state.synthesis
    assert not state.aborted


def test_persona_filter_restricts_active_speakers():
    cfg = _config()
    personas = _personas()
    ledger = TokenLedger(budget_total=cfg.debate.token_budget_total)
    fake = FakeClient(
        ledger=ledger,
        text_for=lambda call, idx: (
            "## Situation\n.\n\n## Complication\n.\n\n## Question\n.\n\n## Answer\n- a\n\n## Empfehlung\n."
            if "SCQA" in call.user_message else "x"
        ),
    )
    engine = DebateEngine(config=cfg, client=fake, personas=personas)
    state = asyncio.run(engine.run("F", persona_filter=["stratege", "cfo-skeptiker"]))
    r1_names = {c.persona for c in state.round(1)}
    assert r1_names == {"stratege", "cfo-skeptiker"}


def test_devils_advocate_receives_devils_reaction_prompt():
    cfg = _config()
    personas = _personas()
    ledger = TokenLedger(budget_total=cfg.debate.token_budget_total)
    fake = FakeClient(
        ledger=ledger,
        text_for=lambda call, idx: (
            "## Situation\n.\n\n## Complication\n.\n\n## Question\n.\n\n## Answer\n- a\n\n## Empfehlung\n."
            if "SCQA" in call.user_message else "x"
        ),
    )
    engine = DebateEngine(config=cfg, client=fake, personas=personas)
    asyncio.run(engine.run("F"))
    devils_r2 = [
        c for c in fake.calls
        if "blinde Flecken" in c.user_message
    ]
    assert len(devils_r2) == 1


def test_memory_entries_passed_into_system_prompt():
    cfg = _config()
    personas = _personas()
    ledger = TokenLedger(budget_total=cfg.debate.token_budget_total)
    fake = FakeClient(
        ledger=ledger,
        text_for=lambda call, idx: (
            "## Situation\n.\n\n## Complication\n.\n\n## Question\n.\n\n## Answer\n- a\n\n## Empfehlung\n."
            if "SCQA" in call.user_message else "x"
        ),
    )
    mem = {"stratege": [{"date": "2026-01-01", "topic": "Reorg X", "summary": "Empfehlung Y"}]}
    engine = DebateEngine(
        config=cfg, client=fake, personas=personas, memory_entries=mem,
    )
    asyncio.run(engine.run("F", persona_filter=["stratege"]))
    stratege_calls = [c for c in fake.calls if "DER STRATEGE" in c.system]
    assert stratege_calls, "expected at least one call to stratege"
    assert any("KONTEXT AUS FRÜHEREN SESSIONS" in c.system for c in stratege_calls)
    assert any("Reorg X" in c.system for c in stratege_calls)


def test_graceful_abort_on_budget_exceeded():
    cfg = _config()
    cfg.debate.token_budget_total = 100
    personas = _personas()
    ledger = TokenLedger(budget_total=cfg.debate.token_budget_total)
    fake = FakeClient(ledger=ledger, fail_after=3)
    engine = DebateEngine(config=cfg, client=fake, personas=personas)
    state = asyncio.run(engine.run("F"))
    assert state.aborted
    assert "forced abort" in state.abort_reason
    # Some contributions should have been recorded before abort.
    assert len(state.contributions) >= 1


def test_convergence_callback_skips_round_3():
    cfg = _config()
    cfg.debate.convergence_detection = True
    personas = _personas()
    ledger = TokenLedger(budget_total=cfg.debate.token_budget_total)

    async def confirm(personas: list[str]) -> bool:
        return True

    def text_for(call: RecordedCall, idx: int) -> str:
        if CONVERGENCE_PROMPT.split("\n")[0][:30] in call.user_message:
            return '{"converged": true, "personas": ["stratege", "cfo-skeptiker", "comms-coach"]}'
        if "SCQA" in call.user_message:
            return "## Situation\n.\n\n## Complication\n.\n\n## Question\n.\n\n## Answer\n- a\n\n## Empfehlung\n."
        return "x"

    fake = FakeClient(ledger=ledger, text_for=text_for)
    engine = DebateEngine(
        config=cfg, client=fake, personas=personas, on_convergence=confirm,
    )
    state = asyncio.run(engine.run("F"))
    assert state.convergence is not None
    assert state.convergence.converged
    assert state.r3_skipped
    assert len(state.round(3)) == 0


def test_parse_convergence_json_handles_extra_text():
    text = "Hier ist das Ergebnis:\n{\"converged\": true, \"personas\": [\"a\", \"b\"]}\nEnde."
    result = _parse_convergence_json(text)
    assert result.converged
    assert result.personas == ["a", "b"]


def test_parse_convergence_json_handles_malformed():
    result = _parse_convergence_json("nichts hier")
    assert not result.converged
    assert result.personas == []


def test_state_attribute_populated_for_partial_archive_on_interrupt():
    """Simulate Ctrl+C mid-engine and verify engine.state holds in-flight contributions."""
    cfg = _config()
    personas = _personas()
    ledger = TokenLedger(budget_total=cfg.debate.token_budget_total)

    @dataclass
    class CancellingClient:
        ledger: TokenLedger
        calls: int = 0

        async def converse(self, *, system, user_message, max_tokens, rag=None, on_text=None):
            self.calls += 1
            if self.calls >= 4:
                raise KeyboardInterrupt
            self.ledger.add(5, 10)
            return ConverseResult(text=f"chunk-{self.calls}", input_tokens=5, output_tokens=10)

    fake = CancellingClient(ledger=ledger)
    engine = DebateEngine(config=cfg, client=fake, personas=personas)
    with pytest.raises(KeyboardInterrupt):
        asyncio.run(engine.run("F"))
    assert engine.state is not None
    assert engine.state.moderator_opening or len(engine.state.contributions) >= 1
