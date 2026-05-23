"""Tests for persona loading and Joshua-profile injection."""
from __future__ import annotations

from pathlib import Path

import pytest

from conductor.personas import JOSHUA_PROFILE, PERSONA_ORDER, PersonaRegistry, load_persona

AGENTS_DIR = Path(__file__).resolve().parents[1] / ".claude" / "agents"


def test_load_persona_parses_frontmatter():
    p = load_persona(AGENTS_DIR / "stratege.md")
    assert p.name == "stratege"
    assert "Strategieberater" in p.description
    assert p.system_prompt.startswith("Du bist DER STRATEGE")


def test_persona_registry_loads_all_six():
    reg = PersonaRegistry.load_all(AGENTS_DIR)
    assert set(reg.personas.keys()) == set(PERSONA_ORDER)
    assert reg.names() == PERSONA_ORDER


def test_all_except_moderator_excludes_moderator():
    reg = PersonaRegistry.load_all(AGENTS_DIR)
    names = [p.name for p in reg.all_except_moderator()]
    assert "moderator" not in names
    assert len(names) == 5


def test_joshua_profile_appended_to_system_prompt():
    reg = PersonaRegistry.load_all(AGENTS_DIR)
    full = reg.get("stratege").with_user_context()
    assert "Strategieberater" in full
    assert JOSHUA_PROFILE in full
    assert "Vermeidet:" in full


def test_memory_entries_injected_into_context():
    reg = PersonaRegistry.load_all(AGENTS_DIR)
    entries = [{"date": "2026-01-01", "topic": "Reorg X", "summary": "Empfehlung war Y"}]
    full = reg.get("stratege").with_user_context(memory_entries=entries)
    assert "KONTEXT AUS FRÜHEREN SESSIONS" in full
    assert "Reorg X" in full
    assert "Empfehlung war Y" in full


def test_load_persona_missing_frontmatter_raises(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text("# no frontmatter\nplain body", encoding="utf-8")
    with pytest.raises(ValueError):
        load_persona(bad)
