"""Per-persona JSON memory (opt-in via --memory flag)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import MemoryConfig
from .debate_engine import SessionState


@dataclass
class MemoryStore:
    config: MemoryConfig

    def _path(self, persona: str) -> Path:
        return Path(self.config.storage_dir) / f"{persona}.json"

    def load_for(self, persona: str) -> list[dict]:
        path = self._path(persona)
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(data, list):
            return []
        return data

    def load_all(self, persona_names: list[str]) -> dict[str, list[dict]]:
        return {name: self.load_for(name) for name in persona_names}

    def append(self, state: SessionState, *, timestamp: datetime | None = None) -> None:
        if state.aborted and not state.contributions:
            return
        ts = (timestamp or datetime.now()).replace(microsecond=0).isoformat()
        Path(self.config.storage_dir).mkdir(parents=True, exist_ok=True)
        for c in state.contributions:
            if c.round_no != 3 or not c.text:
                continue
            entry = {
                "date": ts,
                "topic": state.question[:120],
                "summary": c.text,
            }
            self._append_entry(c.persona, entry)
        if state.synthesis:
            self._append_entry(
                "moderator",
                {
                    "date": ts,
                    "topic": state.question[:120],
                    "summary": _first_paragraph(state.synthesis),
                },
            )

    def _append_entry(self, persona: str, entry: dict) -> None:
        path = self._path(persona)
        current = self.load_for(persona)
        current.append(entry)
        cap = max(1, self.config.max_entries_per_persona)
        if len(current) > cap:
            current = current[-cap:]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")


def _first_paragraph(text: str) -> str:
    for para in text.split("\n\n"):
        para = para.strip()
        if para:
            return para[:400]
    return text[:400]
