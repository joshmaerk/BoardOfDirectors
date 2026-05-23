"""Tests for the YAML config loader."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from conductor.config import Config


def test_load_full_config(tmp_path: Path):
    raw = {
        "api": {"model": "claude-opus-4-7", "max_retries": 5},
        "obsidian": {
            "vault_path": str(tmp_path),
            "allowed_subfolders": ["10-Strategie"],
            "excluded_patterns": ["*.private.md"],
        },
        "debate": {
            "rounds": 3,
            "token_budget_total": 50_000,
            "token_budget_per_persona": {"opening": 500, "reaction": 250, "final": 100},
            "moderator_synthesis_tokens": 1500,
            "convergence_detection": False,
        },
        "archive": {"output_dir": str(tmp_path / "arc")},
        "memory": {
            "enabled_by_default": True,
            "storage_dir": str(tmp_path / "mem"),
            "max_entries_per_persona": 20,
        },
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    cfg = Config.load(path)
    assert cfg.api.model == "claude-opus-4-7"
    assert cfg.api.max_retries == 5
    assert cfg.obsidian.allowed_subfolders == ["10-Strategie"]
    assert cfg.debate.token_budget_total == 50_000
    assert cfg.debate.token_budget_per_persona.opening == 500
    assert cfg.debate.convergence_detection is False
    assert cfg.memory.enabled_by_default is True
    assert cfg.memory.max_entries_per_persona == 20


def test_load_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        Config.load(tmp_path / "nope.yaml")


def test_defaults_apply_for_missing_sections(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text("api:\n  model: 'claude-opus-4-7'\n", encoding="utf-8")
    cfg = Config.load(path)
    assert cfg.debate.token_budget_total == 80_000
    assert cfg.archive.format == "markdown"
