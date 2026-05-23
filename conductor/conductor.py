"""Session orchestrator: wires config, personas, client, engine, archive, memory."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path

import click

from .archive import Archive
from .client import ClaudeClient, TokenLedger
from .config import Config
from .debate_engine import DebateEngine, SessionState
from .memory import MemoryStore
from .personas import PersonaRegistry
from .rag import RagTool
from .streaming import RoundtableDisplay

USE_CASE_KEYWORDS = {
    "Stakeholder-Kommunikation": (
        "vorstand",
        "betriebsrat",
        "kommunikation",
        "e-mail",
        "email",
        "präsentation",
        "stakeholder",
        "gespräch",
        "aufsichtsrat",
    ),
}


def detect_use_case(question: str) -> str:
    q = question.lower()
    for label, kws in USE_CASE_KEYWORDS.items():
        if any(k in q for k in kws):
            return label
    return "Strategische Führungsentscheidung"


@dataclass
class SessionRunner:
    config: Config

    async def run(
        self,
        question: str,
        *,
        memory: bool = False,
        persona_filter: list[str] | None = None,
        display: RoundtableDisplay | None = None,
    ) -> tuple[SessionState, Path]:
        personas = PersonaRegistry.load_all()
        ledger = TokenLedger(budget_total=self.config.debate.token_budget_total)
        client = ClaudeClient(model=self.config.api.model, ledger=ledger)
        rag = RagTool(self.config.obsidian)

        memory_entries: dict[str, list[dict]] = {}
        store: MemoryStore | None = None
        if memory:
            store = MemoryStore(self.config.memory)
            memory_entries = store.load_all(personas.names())

        if display is not None:
            display.ledger = ledger

        engine = DebateEngine(
            config=self.config,
            client=client,
            personas=personas,
            rag=rag,
            display=display,
            memory_entries=memory_entries,
            on_convergence=_prompt_skip_r3,
        )

        started = time.monotonic()
        archive = Archive(self.config.archive)
        interrupted: BaseException | None = None
        try:
            state = await engine.run(question, persona_filter=persona_filter)
        except (KeyboardInterrupt, asyncio.CancelledError) as e:
            state = engine.state or SessionState(question=question)
            state.aborted = True
            state.abort_reason = "Abbruch durch Benutzer (Ctrl+C)"
            interrupted = e
        duration = time.monotonic() - started
        path = archive.write(
            state,
            ledger,
            use_case=detect_use_case(question),
            memory_loaded=memory,
            persona_names=personas.names(),
            duration_seconds=duration,
        )
        if store is not None and not state.aborted:
            store.append(state)
        if interrupted is not None:
            raise interrupted
        return state, path


async def _prompt_skip_r3(personas: list[str]) -> bool:
    msg = (
        f"Konvergenz erkannt zwischen: {', '.join(personas) or 'mehreren Personen'}. "
        "Round 3 überspringen?"
    )
    return click.confirm(msg, default=False)
