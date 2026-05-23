"""Tests for the per-persona JSON memory store."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from conductor.config import MemoryConfig
from conductor.debate_engine import PersonaContribution, SessionState
from conductor.memory import MemoryStore


def _state_with_finale(question: str = "Frage X") -> SessionState:
    state = SessionState(question=question)
    state.contributions.append(
        PersonaContribution(
            persona="stratege",
            display_name="Der Stratege",
            round_no=3,
            text="Finale Position des Strategen.",
        )
    )
    state.synthesis = "## Situation\nS.\n\n## Answer\nA."
    return state


def test_memory_append_writes_files_per_persona(tmp_path: Path):
    store = MemoryStore(MemoryConfig(storage_dir=tmp_path, max_entries_per_persona=10))
    store.append(_state_with_finale(), timestamp=datetime(2026, 5, 22, 10, 0))
    files = sorted(p.name for p in tmp_path.glob("*.json"))
    assert "stratege.json" in files
    assert "moderator.json" in files
    data = json.loads((tmp_path / "stratege.json").read_text(encoding="utf-8"))
    assert data[0]["topic"] == "Frage X"
    assert data[0]["summary"].startswith("Finale Position")


def test_memory_load_for_returns_empty_when_missing(tmp_path: Path):
    store = MemoryStore(MemoryConfig(storage_dir=tmp_path))
    assert store.load_for("stratege") == []


def test_memory_fifo_caps_entries(tmp_path: Path):
    store = MemoryStore(MemoryConfig(storage_dir=tmp_path, max_entries_per_persona=2))
    for i in range(5):
        store.append(_state_with_finale(question=f"F{i}"))
    data = json.loads((tmp_path / "stratege.json").read_text(encoding="utf-8"))
    assert len(data) == 2
    assert data[-1]["topic"] == "F4"


def test_memory_load_all_returns_dict_keyed_by_persona(tmp_path: Path):
    store = MemoryStore(MemoryConfig(storage_dir=tmp_path))
    store.append(_state_with_finale())
    loaded = store.load_all(["stratege", "moderator", "comms-coach"])
    assert set(loaded.keys()) == {"stratege", "moderator", "comms-coach"}
    assert loaded["stratege"]
    assert loaded["comms-coach"] == []
