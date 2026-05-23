"""Obsidian-vault RAG via whitelisted file reading."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path

from .config import ObsidianConfig

MAX_NOTE_BYTES = 50_000

TOOL_SCHEMA = {
    "name": "read_obsidian_note",
    "description": (
        "Read a markdown note from the user's Obsidian vault. "
        "Use only when the note is clearly relevant to your contribution. "
        "Pass the path relative to the vault root."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "relative_path": {
                "type": "string",
                "description": (
                    "Path relative to the vault root, e.g. "
                    "'20-OE-Vertriebssteuerung/VC-Reorg-Status.md'."
                ),
            }
        },
        "required": ["relative_path"],
    },
}


@dataclass
class RagTool:
    config: ObsidianConfig

    def is_allowed(self, relative_path: str) -> bool:
        if not relative_path:
            return False
        rel = Path(relative_path)
        if rel.is_absolute() or ".." in rel.parts:
            return False
        if not self.config.allowed_subfolders:
            return False
        normalized = relative_path.replace("\\", "/")
        in_whitelist = any(
            normalized == sub or normalized.startswith(f"{sub}/")
            for sub in self.config.allowed_subfolders
        )
        if not in_whitelist:
            return False
        for pattern in self.config.excluded_patterns:
            if fnmatch.fnmatch(normalized, pattern):
                return False
        return True

    def read(self, relative_path: str) -> str:
        if not self.is_allowed(relative_path):
            return f"[blocked: path '{relative_path}' is outside the whitelisted vault scope]"
        full = self.config.vault_path / relative_path
        if not full.exists() or not full.is_file():
            return f"[not found: {relative_path}]"
        try:
            data = full.read_bytes()[:MAX_NOTE_BYTES]
        except OSError as e:
            return f"[read error: {e}]"
        return data.decode("utf-8", errors="replace")
