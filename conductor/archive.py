"""Markdown archive writer for completed roundtable sessions."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

from .client import TokenLedger
from .config import ArchiveConfig
from .debate_engine import SessionState

_SLUG_RE = re.compile(r"[^a-z0-9]+")
ROUND_LABELS = {
    1: "Opening Statements",
    2: "Reaction Round",
    3: "Final Position",
}


def slugify(text: str, max_words: int = 6) -> str:
    words = _SLUG_RE.sub(" ", text.lower()).split()
    return "-".join(words[:max_words]) or "session"


@dataclass
class Archive:
    config: ArchiveConfig

    def write(
        self,
        state: SessionState,
        ledger: TokenLedger,
        *,
        use_case: str = "Unbestimmt",
        memory_loaded: bool = False,
        persona_names: list[str] | None = None,
        duration_seconds: float = 0.0,
        timestamp: datetime | None = None,
    ) -> Path:
        ts = timestamp or datetime.now()
        slug = slugify(state.question)
        filename = f"{ts.strftime('%Y-%m-%d_%H-%M')}_{slug}.md"
        out_dir = Path(self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / filename
        path.write_text(self._render(
            state=state,
            ledger=ledger,
            use_case=use_case,
            memory_loaded=memory_loaded,
            persona_names=persona_names or [],
            duration_seconds=duration_seconds,
            timestamp=ts,
        ), encoding="utf-8")
        return path

    def _render(
        self,
        *,
        state: SessionState,
        ledger: TokenLedger,
        use_case: str,
        memory_loaded: bool,
        persona_names: list[str],
        duration_seconds: float,
        timestamp: datetime,
    ) -> str:
        fm = {
            "date": timestamp.replace(microsecond=0).isoformat(),
            "topic": state.question[:120],
            "question": state.question,
            "use_case": use_case,
            "personas": persona_names,
            "memory_loaded": memory_loaded,
            "tokens_input": ledger.input,
            "tokens_output": ledger.output,
            "budget_status": ledger.status,
            "duration_seconds": round(duration_seconds, 1),
            "compliance_status": "user-responsibility",
            "aborted": state.aborted,
        }
        if state.aborted and state.abort_reason:
            fm["abort_reason"] = state.abort_reason
        if state.convergence:
            fm["convergence_detected"] = state.convergence.converged
            if state.convergence.converged:
                fm["convergence_personas"] = state.convergence.personas
        if state.r3_skipped:
            fm["round3_skipped"] = True

        frontmatter = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()

        lines: list[str] = ["---", frontmatter, "---", ""]
        title_topic = state.question[:80].strip()
        lines.append(f"# Roundtable: {title_topic}")
        lines.append("")
        lines.append("## Frage")
        lines.append(state.question)
        lines.append("")
        if state.moderator_opening:
            lines.append("## Moderator Opening")
            lines.append(state.moderator_opening)
            lines.append("")
        for r in (1, 2, 3):
            block = state.round(r)
            if not block:
                continue
            lines.append(f"## Round {r} - {ROUND_LABELS[r]}")
            for c in block:
                lines.append(f"### {c.display_name}")
                lines.append(c.text)
                lines.append("")
        if state.r3_skipped:
            lines.append("> Round 3 wurde nach Konvergenz-Erkennung übersprungen.")
            lines.append("")
        if state.synthesis:
            lines.append("## Round 4 - Moderator-Synthese (SCQA)")
            lines.append(state.synthesis)
            lines.append("")
        used = state.used_paths_by_persona()
        if used:
            lines.append("## Gelesene Quellen (Obsidian)")
            for persona, paths in used.items():
                for p in paths:
                    lines.append(f"- {p} ({persona})")
            lines.append("")
        if state.aborted:
            lines.append("> Session wurde nach Token-Budget-Überschreitung abgebrochen.")
            lines.append(f"> Grund: {state.abort_reason}")
            lines.append("")
        return "\n".join(lines)

    def list(self) -> list[Path]:
        out_dir = Path(self.config.output_dir)
        if not out_dir.exists():
            return []
        return sorted(p for p in out_dir.glob("*.md") if p.is_file())
