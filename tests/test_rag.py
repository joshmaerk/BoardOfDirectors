"""Tests for the Obsidian RAG whitelist."""
from __future__ import annotations

from pathlib import Path

import pytest

from conductor.config import ObsidianConfig
from conductor.rag import RagTool


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    (tmp_path / "10-Strategie").mkdir()
    (tmp_path / "10-Strategie" / "Note.md").write_text("public content", encoding="utf-8")
    (tmp_path / "10-Strategie" / "secret.private.md").write_text("secret", encoding="utf-8")
    (tmp_path / "99-Privates").mkdir()
    (tmp_path / "99-Privates" / "Tagebuch.md").write_text("private", encoding="utf-8")
    return tmp_path


@pytest.fixture
def tool(vault: Path) -> RagTool:
    cfg = ObsidianConfig(
        vault_path=vault,
        allowed_subfolders=["10-Strategie"],
        excluded_patterns=["*.private.md"],
    )
    return RagTool(cfg)


def test_subfolder_whitelist_enforced(tool: RagTool):
    assert tool.is_allowed("10-Strategie/Note.md")
    assert not tool.is_allowed("99-Privates/Tagebuch.md")
    blocked = tool.read("99-Privates/Tagebuch.md")
    assert blocked.startswith("[blocked")


def test_excluded_patterns_block(tool: RagTool):
    assert not tool.is_allowed("10-Strategie/secret.private.md")
    assert tool.read("10-Strategie/secret.private.md").startswith("[blocked")


def test_absolute_path_blocked(tool: RagTool):
    assert not tool.is_allowed("/etc/passwd")


def test_parent_traversal_blocked(tool: RagTool):
    assert not tool.is_allowed("10-Strategie/../99-Privates/Tagebuch.md")


def test_read_returns_content_for_allowed(tool: RagTool):
    content = tool.read("10-Strategie/Note.md")
    assert content == "public content"


def test_read_returns_not_found_when_path_missing(tool: RagTool):
    msg = tool.read("10-Strategie/missing.md")
    assert msg.startswith("[not found")


def test_no_whitelist_blocks_everything(vault: Path):
    cfg = ObsidianConfig(vault_path=vault, allowed_subfolders=[], excluded_patterns=[])
    tool = RagTool(cfg)
    assert not tool.is_allowed("10-Strategie/Note.md")
