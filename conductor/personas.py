"""Persona loader for .claude/agents/*.md files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

JOSHUA_PROFILE = """\
KONTEXT ZU JOSHUA (Auftraggeber des Boards):
- Position: GBL Vertriebssteuerung, RLB OÖ (ECB-supervised Landesbank, Sektorverbund)
- Spanne: 250 FTE, fünf Organisationseinheiten (drei Stäbe: VE/VT/VC, zwei Abteilungen: OKM/VVF)
- P&L-Verantwortung: DB I/II/III, Provisionsertrag, CLV, Vertriebseffizienz
- Karriereziel: C-Level (CDO primär, CMO sekundär, COO tertiär) in kooperativem Bankenkontext
- Regulatorischer Rahmen: BWG §39/39a, EBA/GL/2021/05, DORA, CRR III/CRD VI, EZB Fit & Proper, Genossenschaftsgesetz
- Aktuelle Themen: VC-Integration als neuer Stab, GB-Operating-Model V3, KPI-Treiberbaum
- Stil-Präferenz: McKinsey/BCG-Rigor, SCQA, Pyramid Principle, Bericht-Ton statt Handbuch-Ton
- Vermeidet: Em-Dashes, „Single Source of Truth", „integriert", „konsistent"
- Status-Bezeichner: immer grün/gelb/rot
"""

PERSONA_ORDER = [
    "stratege",
    "cfo-skeptiker",
    "banking-veteran",
    "devils-advocate",
    "comms-coach",
    "moderator",
]

AVATARS = {
    "stratege": "♟",
    "cfo-skeptiker": "$",
    "banking-veteran": "§",
    "devils-advocate": "?",
    "comms-coach": "✉",
    "moderator": "⚖",
}

DISPLAY_NAMES = {
    "stratege": "Der Stratege",
    "cfo-skeptiker": "Der CFO-Skeptiker",
    "banking-veteran": "Der Banking Veteran",
    "devils-advocate": "Der Devil's Advocate",
    "comms-coach": "Der Communications Coach",
    "moderator": "Der Moderator",
}

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


@dataclass
class Persona:
    name: str
    description: str
    system_prompt: str
    avatar: str = "•"
    display_name: str = ""

    def with_user_context(
        self,
        profile: str = JOSHUA_PROFILE,
        memory_entries: list[dict] | None = None,
    ) -> str:
        parts = [self.system_prompt, profile]
        if memory_entries:
            lines = ["KONTEXT AUS FRÜHEREN SESSIONS:"]
            for entry in memory_entries:
                date = entry.get("date", "")
                topic = entry.get("topic", "")
                summary = entry.get("summary", "")
                lines.append(f"- [{date}] {topic}: {summary}")
            parts.append("\n".join(lines))
        return "\n\n".join(parts)


def _parse_md(text: str) -> tuple[dict, str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError("Agent file is missing YAML frontmatter (--- ... ---)")
    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2).strip()
    return fm, body


def load_persona(path: Path) -> Persona:
    text = path.read_text(encoding="utf-8")
    fm, body = _parse_md(text)
    name = fm.get("name") or path.stem
    desc = fm.get("description") or ""
    return Persona(
        name=name,
        description=desc,
        system_prompt=body,
        avatar=AVATARS.get(name, "•"),
        display_name=DISPLAY_NAMES.get(name, name),
    )


@dataclass
class PersonaRegistry:
    personas: dict[str, Persona] = field(default_factory=dict)

    @classmethod
    def load_all(cls, agents_dir: Path | str = ".claude/agents") -> PersonaRegistry:
        agents_dir = Path(agents_dir)
        if not agents_dir.exists():
            raise FileNotFoundError(f"Agents directory not found: {agents_dir}")
        found: dict[str, Persona] = {}
        for path in agents_dir.glob("*.md"):
            p = load_persona(path)
            found[p.name] = p
        ordered: dict[str, Persona] = {}
        for name in PERSONA_ORDER:
            if name in found:
                ordered[name] = found.pop(name)
        for name, p in found.items():
            ordered[name] = p
        return cls(personas=ordered)

    def get(self, name: str) -> Persona:
        if name not in self.personas:
            raise KeyError(f"Persona not found: {name}")
        return self.personas[name]

    def all_except_moderator(self) -> list[Persona]:
        return [p for n, p in self.personas.items() if n != "moderator"]

    def names(self) -> list[str]:
        return list(self.personas.keys())
