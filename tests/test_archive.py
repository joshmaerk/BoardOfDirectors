"""Tests for the markdown archive writer."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import yaml

from conductor.archive import Archive, slugify
from conductor.client import TokenLedger
from conductor.config import ArchiveConfig
from conductor.debate_engine import (
    ConvergenceResult,
    PersonaContribution,
    SessionState,
)


def _make_state() -> SessionState:
    state = SessionState(question="Wie steuere ich die VC-Integration?")
    state.moderator_opening = "Frame: Sequenzierung und Stakeholder."
    for round_no, text in [(1, "Opening"), (2, "Reaktion"), (3, "Finale Position")]:
        state.contributions.append(
            PersonaContribution(
                persona="stratege",
                display_name="Der Stratege",
                round_no=round_no,
                text=f"{text} vom Strategen",
                used_paths=["10-Strategie/note.md"] if round_no == 1 else [],
                input_tokens=100,
                output_tokens=50,
            )
        )
    state.synthesis = (
        "## Situation\nLage.\n\n"
        "## Complication\nKomplikation.\n\n"
        "## Question\nFrage.\n\n"
        "## Answer\n- Arg 1\n- Arg 2\n- Arg 3\n\n"
        "## Empfehlung\nKurze Empfehlung."
    )
    state.convergence = ConvergenceResult(converged=False)
    return state


def _parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    assert m, "frontmatter missing"
    return yaml.safe_load(m.group(1))


def test_slugify_basic():
    assert slugify("Wie steuere ich die VC-Integration?") == "wie-steuere-ich-die-vc-integration"
    assert slugify("") == "session"


def test_archive_writes_file_with_expected_filename(tmp_path: Path):
    arc = Archive(ArchiveConfig(output_dir=tmp_path))
    ledger = TokenLedger(budget_total=80_000, input=500, output=2000)
    ts = datetime(2026, 5, 22, 14, 30)
    path = arc.write(
        _make_state(),
        ledger,
        use_case="Strategische Führungsentscheidung",
        memory_loaded=False,
        persona_names=["stratege", "moderator"],
        duration_seconds=42.0,
        timestamp=ts,
    )
    assert path.exists()
    assert path.name.startswith("2026-05-22_14-30_")
    assert path.suffix == ".md"


def test_scqa_headings_present(tmp_path: Path):
    arc = Archive(ArchiveConfig(output_dir=tmp_path))
    ledger = TokenLedger(budget_total=80_000, output=1000)
    path = arc.write(_make_state(), ledger, persona_names=["stratege"])
    text = path.read_text(encoding="utf-8")
    assert re.search(r"^## Situation\b", text, re.MULTILINE)
    assert re.search(r"^## Complication\b", text, re.MULTILINE)
    assert re.search(r"^## Question\b", text, re.MULTILINE)
    assert re.search(r"^## Answer\b", text, re.MULTILINE)
    assert re.search(r"^## Empfehlung\b", text, re.MULTILINE)


def test_frontmatter_contains_token_counts(tmp_path: Path):
    arc = Archive(ArchiveConfig(output_dir=tmp_path))
    ledger = TokenLedger(budget_total=80_000, input=321, output=4567)
    path = arc.write(_make_state(), ledger, persona_names=["stratege"])
    fm = _parse_frontmatter(path.read_text(encoding="utf-8"))
    assert fm["tokens_input"] == 321
    assert fm["tokens_output"] == 4567
    assert fm["budget_status"] in {"grün", "gelb", "rot"}


def test_compliance_status_in_frontmatter(tmp_path: Path):
    arc = Archive(ArchiveConfig(output_dir=tmp_path))
    ledger = TokenLedger(budget_total=80_000)
    path = arc.write(_make_state(), ledger, persona_names=["stratege"])
    fm = _parse_frontmatter(path.read_text(encoding="utf-8"))
    assert fm["compliance_status"] == "user-responsibility"


def test_archive_includes_used_obsidian_sources(tmp_path: Path):
    arc = Archive(ArchiveConfig(output_dir=tmp_path))
    ledger = TokenLedger(budget_total=80_000)
    path = arc.write(_make_state(), ledger, persona_names=["stratege"])
    text = path.read_text(encoding="utf-8")
    assert "## Gelesene Quellen (Obsidian)" in text
    assert "10-Strategie/note.md" in text


def test_budget_status_rot_when_overshoot(tmp_path: Path):
    arc = Archive(ArchiveConfig(output_dir=tmp_path))
    ledger = TokenLedger(budget_total=1000, output=950)
    path = arc.write(_make_state(), ledger, persona_names=["stratege"])
    fm = _parse_frontmatter(path.read_text(encoding="utf-8"))
    assert fm["budget_status"] == "rot"
