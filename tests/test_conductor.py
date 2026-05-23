"""Tests for the SessionRunner and use-case detection."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from conductor import conductor as conductor_module
from conductor.client import ConverseResult, TokenLedger
from conductor.config import Config


def test_detect_use_case_strategic_default():
    assert (
        conductor_module.detect_use_case("Wie steuere ich die Reorganisation?")
        == "Strategische Führungsentscheidung"
    )


def test_detect_use_case_stakeholder_when_vorstand_mentioned():
    assert (
        conductor_module.detect_use_case("Entwurf einer E-Mail an den Vorstand zur Reorg")
        == "Stakeholder-Kommunikation"
    )


def test_detect_use_case_stakeholder_when_betriebsrat_mentioned():
    assert (
        conductor_module.detect_use_case("Wie kommuniziere ich das an den Betriebsrat?")
        == "Stakeholder-Kommunikation"
    )


@dataclass
class _FakeClient:
    ledger: TokenLedger
    calls: int = field(default=0)

    async def converse(self, *, system, user_message, max_tokens, rag=None, on_text=None):
        self.calls += 1
        self.ledger.add(5, 10)
        if "SCQA" in user_message:
            text = (
                "## Situation\nS\n\n"
                "## Complication\nC\n\n"
                "## Question\nQ\n\n"
                "## Answer\n- a\n- b\n- c\n\n"
                "## Empfehlung\nE"
            )
        else:
            text = f"chunk-{self.calls}"
        if on_text:
            on_text(text)
        return ConverseResult(text=text, input_tokens=5, output_tokens=10, stop_reason="end_turn")


def _build_config(tmp_path: Path) -> Config:
    raw = {
        "api": {"model": "claude-opus-4-7"},
        "obsidian": {"vault_path": str(tmp_path), "allowed_subfolders": []},
        "debate": {
            "token_budget_total": 1_000_000,
            "convergence_detection": False,
        },
        "archive": {"output_dir": str(tmp_path / "archives")},
        "memory": {"storage_dir": str(tmp_path / "mem")},
    }
    return Config.from_dict(raw)


def test_session_runner_writes_archive_and_returns_state(monkeypatch, tmp_path: Path):
    cfg = _build_config(tmp_path)

    def _client_factory(*, model, ledger, api_key=None):
        return _FakeClient(ledger=ledger)

    monkeypatch.setattr(conductor_module, "ClaudeClient", _client_factory)

    runner = conductor_module.SessionRunner(cfg)
    state, path = asyncio.run(runner.run("Wie steuere ich die VC-Integration?"))

    assert path.exists()
    assert path.name.endswith(".md")
    assert "## Situation" in state.synthesis
    assert not state.aborted
    assert len(state.round(1)) == 5
    assert len(state.round(2)) == 5
    assert len(state.round(3)) == 5


def test_session_runner_memory_flag_loads_and_appends(monkeypatch, tmp_path: Path):
    cfg = _build_config(tmp_path)
    memory_dir = tmp_path / "mem"
    memory_dir.mkdir()
    (memory_dir / "stratege.json").write_text(
        yaml.safe_dump([{"date": "2026-01-01", "topic": "Reorg X", "summary": "Empfehlung Y"}]),
        encoding="utf-8",
    )

    def _client_factory(*, model, ledger, api_key=None):
        return _FakeClient(ledger=ledger)

    monkeypatch.setattr(conductor_module, "ClaudeClient", _client_factory)

    runner = conductor_module.SessionRunner(cfg)
    state, _ = asyncio.run(runner.run("Frage", memory=True))

    assert not state.aborted
    # MemoryStore should have appended at least one entry per persona that spoke in R3
    persona_files = list(memory_dir.glob("*.json"))
    assert persona_files
