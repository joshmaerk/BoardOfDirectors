"""Tests for the click CLI."""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from conductor.cli import main


def _write_config(tmp_path: Path) -> Path:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump(
            {
                "api": {"model": "claude-opus-4-7"},
                "obsidian": {"vault_path": str(tmp_path), "allowed_subfolders": []},
                "debate": {"token_budget_total": 1000},
                "archive": {"output_dir": str(tmp_path / "archives")},
                "memory": {"storage_dir": str(tmp_path / "mem")},
            }
        ),
        encoding="utf-8",
    )
    return cfg_path


def test_main_shows_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Personal Board of Directors" in result.output
    assert "ask" in result.output
    assert "archive" in result.output


def test_ask_without_question_or_topic_file_errors():
    runner = CliRunner()
    result = runner.invoke(main, ["ask"])
    assert result.exit_code != 0
    assert "Frage" in result.output or "topic-file" in result.output


def test_ask_missing_config_yields_clean_error(tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--config", str(tmp_path / "nope.yaml"), "ask", "Testfrage"],
    )
    assert result.exit_code == 2
    assert "Config" in result.output or "not found" in result.output


def test_archive_list_on_empty_dir(tmp_path: Path):
    cfg = _write_config(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(cfg), "archive", "list"])
    assert result.exit_code == 0
    assert "Keine Archive" in result.output


def test_archive_list_shows_existing_files(tmp_path: Path):
    cfg = _write_config(tmp_path)
    archive_dir = tmp_path / "archives"
    archive_dir.mkdir()
    (archive_dir / "2026-05-22_14-30_test.md").write_text("# stub", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(cfg), "archive", "list"])
    assert result.exit_code == 0
    assert "2026-05-22_14-30_test.md" in result.output


def test_archive_show_missing_file_errors(tmp_path: Path):
    cfg = _write_config(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(cfg), "archive", "show", "nope.md"])
    assert result.exit_code != 0
    assert "nicht gefunden" in result.output


def test_archive_show_renders_existing_file(tmp_path: Path):
    cfg = _write_config(tmp_path)
    archive_dir = tmp_path / "archives"
    archive_dir.mkdir()
    body = "# Test-Archiv\n\nInhalt"
    (archive_dir / "demo.md").write_text(body, encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(cfg), "archive", "show", "demo.md"])
    assert result.exit_code == 0
    assert "Test-Archiv" in result.output
