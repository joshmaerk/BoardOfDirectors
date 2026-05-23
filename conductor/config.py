"""YAML configuration loader."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ApiConfig:
    model: str = "claude-opus-4-7"
    max_retries: int = 3


@dataclass
class ObsidianConfig:
    vault_path: Path = field(default_factory=Path)
    allowed_subfolders: list[str] = field(default_factory=list)
    excluded_patterns: list[str] = field(default_factory=list)


@dataclass
class TokenBudget:
    opening: int = 400
    reaction: int = 300
    final: int = 150


@dataclass
class DebateConfig:
    rounds: int = 3
    token_budget_total: int = 80_000
    token_budget_per_persona: TokenBudget = field(default_factory=TokenBudget)
    moderator_synthesis_tokens: int = 1200
    convergence_detection: bool = True


@dataclass
class ArchiveConfig:
    output_dir: Path = field(default_factory=lambda: Path("./board-archives"))
    format: str = "markdown"
    include_token_counts: bool = True


@dataclass
class MemoryConfig:
    enabled_by_default: bool = False
    storage_dir: Path = field(default_factory=lambda: Path("./board-archives/.memory"))
    max_entries_per_persona: int = 50


@dataclass
class Config:
    api: ApiConfig = field(default_factory=ApiConfig)
    obsidian: ObsidianConfig = field(default_factory=ObsidianConfig)
    debate: DebateConfig = field(default_factory=DebateConfig)
    archive: ArchiveConfig = field(default_factory=ArchiveConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)

    @classmethod
    def load(cls, path: Path | str = "config.yaml") -> "Config":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"Config file not found: {path}. "
                f"Kopiere config.yaml.example nach config.yaml."
            )
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Config":
        api = ApiConfig(**(raw.get("api") or {}))
        obs_raw = raw.get("obsidian") or {}
        obs = ObsidianConfig(
            vault_path=Path(obs_raw.get("vault_path", "")),
            allowed_subfolders=list(obs_raw.get("allowed_subfolders") or []),
            excluded_patterns=list(obs_raw.get("excluded_patterns") or []),
        )
        deb_raw = raw.get("debate") or {}
        budget = TokenBudget(**(deb_raw.get("token_budget_per_persona") or {}))
        debate = DebateConfig(
            rounds=deb_raw.get("rounds", 3),
            token_budget_total=deb_raw.get("token_budget_total", 80_000),
            token_budget_per_persona=budget,
            moderator_synthesis_tokens=deb_raw.get("moderator_synthesis_tokens", 1200),
            convergence_detection=deb_raw.get("convergence_detection", True),
        )
        arc_raw = raw.get("archive") or {}
        archive = ArchiveConfig(
            output_dir=Path(arc_raw.get("output_dir", "./board-archives")),
            format=arc_raw.get("format", "markdown"),
            include_token_counts=arc_raw.get("include_token_counts", True),
        )
        mem_raw = raw.get("memory") or {}
        memory = MemoryConfig(
            enabled_by_default=mem_raw.get("enabled_by_default", False),
            storage_dir=Path(mem_raw.get("storage_dir", "./board-archives/.memory")),
            max_entries_per_persona=mem_raw.get("max_entries_per_persona", 50),
        )
        return cls(api=api, obsidian=obs, debate=debate, archive=archive, memory=memory)
