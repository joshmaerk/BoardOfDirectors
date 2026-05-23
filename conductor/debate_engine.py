"""Roundtable orchestrator: R1 parallel, R2 sequential, R3 parallel, R4 synthesis."""
from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Optional

from .client import BudgetExceededError, ClaudeClient
from .config import Config
from .personas import Persona, PersonaRegistry
from .rag import RagTool
from .streaming import RoundtableDisplay

MODERATOR_OPEN_PROMPT = (
    "Eröffne den Roundtable in 1-2 Sätzen. Frame die Frage. Kein SCQA, das kommt am Ende.\n\n"
    "Frage: {question}"
)
OPENING_PROMPT = (
    "Eröffne den Roundtable mit deiner ersten Position zur folgenden Frage. "
    "Bleibe stilistisch konsequent in deiner Rolle. Max. 2-4 Sätze.\n\n"
    "Frage: {question}"
)
REACTION_PROMPT = (
    "Du hast die Opening Statements der anderen Personen gehört (unten). "
    "Reagiere auf ein oder zwei Statements, die du am stärksten teilst oder ablehnst. "
    "Nimm Bezug auf den Namen. Max. 2-3 Sätze.\n\n"
    "Frage: {question}\n\n"
    "Opening Statements:\n{round1_summary}"
)
DEVILS_REACTION_PROMPT = (
    "Du hast die Opening Statements gehört (unten). "
    "Wo siehst du blinde Flecken? Welche Annahme prüft hier niemand? "
    "Sei präzise, nicht zynisch. Max. 2-3 Sätze.\n\n"
    "Frage: {question}\n\n"
    "Opening Statements:\n{round1_summary}"
)
FINAL_PROMPT = (
    "Verdichte deine finale Position in genau einem Satz. "
    "Diese Aussage geht in die Synthese.\n\n"
    "Frage: {question}\n\n"
    "Bisheriger Verlauf:\n{transcript}"
)
SYNTHESIS_PROMPT = (
    "Synthetisiere den gesamten Roundtable als SCQA-Briefing. "
    "Verwende EXAKT diese Headings in dieser Reihenfolge: "
    "## Situation, ## Complication, ## Question, ## Answer. "
    "Unter Answer drei tragende Argumente als Bullet-Liste. "
    "Schließe mit einem Absatz ## Empfehlung (1-2 Sätze, Bericht-Ton).\n\n"
    "Frage: {question}\n\n"
    "Vollständiger Verlauf:\n{transcript}"
)
CONVERGENCE_PROMPT = (
    "Prüfe die folgenden Reaktions-Statements der Personen aus Runde 2. "
    "Teilen DREI ODER MEHR Personen eine substanziell deckungsgleiche Position? "
    "Antworte AUSSCHLIESSLICH als JSON, ohne weiteren Text: "
    '{{"converged": true|false, "personas": ["name1", "name2", ...]}}.\n\n'
    "Reaktionen:\n{round2_summary}"
)


@dataclass
class PersonaContribution:
    persona: str
    display_name: str
    round_no: int
    text: str
    used_paths: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class ConvergenceResult:
    converged: bool
    personas: list[str] = field(default_factory=list)


@dataclass
class SessionState:
    question: str
    moderator_opening: str = ""
    contributions: list[PersonaContribution] = field(default_factory=list)
    synthesis: str = ""
    convergence: ConvergenceResult | None = None
    r3_skipped: bool = False
    aborted: bool = False
    abort_reason: str = ""

    def round(self, n: int) -> list[PersonaContribution]:
        return [c for c in self.contributions if c.round_no == n]

    def used_paths_by_persona(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for c in self.contributions:
            if not c.used_paths:
                continue
            out.setdefault(c.persona, [])
            for p in c.used_paths:
                if p not in out[c.persona]:
                    out[c.persona].append(p)
        return out


SkipR3Callback = Callable[[list[str]], Awaitable[bool]]


@dataclass
class DebateEngine:
    config: Config
    client: ClaudeClient
    personas: PersonaRegistry
    rag: RagTool | None = None
    display: RoundtableDisplay | None = None
    memory_entries: dict[str, list[dict]] = field(default_factory=dict)
    on_convergence: Optional[SkipR3Callback] = None
    state: SessionState | None = field(default=None, init=False)

    def _system_for(self, persona: Persona) -> str:
        mem = self.memory_entries.get(persona.name)
        return persona.with_user_context(memory_entries=mem)

    async def run(
        self,
        question: str,
        persona_filter: list[str] | None = None,
    ) -> SessionState:
        state = SessionState(question=question)
        self.state = state
        non_mod = self.personas.all_except_moderator()
        if persona_filter:
            allowed = {n for n in persona_filter if n != "moderator"}
            non_mod = [p for p in non_mod if p.name in allowed]
            if not non_mod:
                raise ValueError("persona_filter excludes every non-moderator persona")
        moderator = self.personas.get("moderator")

        try:
            await self._moderator_open(moderator, question, state)
            await self._round1(non_mod, question, state)
            await self._round2(non_mod, question, state)
            if self.config.debate.convergence_detection:
                await self._check_convergence(moderator, state)
            if not state.r3_skipped:
                await self._round3(non_mod, question, state)
            await self._synthesis(moderator, question, state)
        except BudgetExceededError as e:
            state.aborted = True
            state.abort_reason = str(e)
        return state

    async def _moderator_open(
        self, moderator: Persona, question: str, state: SessionState
    ) -> None:
        if self.display:
            self.display.set_header(f"Round 0/4 - Moderator Opening")
            self.display.reset_panes()
            self.display.add_pane(
                moderator.name, moderator.display_name, moderator.avatar, style="cyan"
            )
        appender = self.display.appender(moderator.name) if self.display else None
        result = await self.client.converse(
            system=self._system_for(moderator),
            user_message=MODERATOR_OPEN_PROMPT.format(question=question),
            max_tokens=200,
            rag=None,
            on_text=appender,
        )
        state.moderator_opening = result.text.strip()

    async def _round1(
        self, personas: list[Persona], question: str, state: SessionState
    ) -> None:
        if self.display:
            self.display.set_header("Round 1/4 - Opening Statements")
            self.display.reset_panes()
            for p in personas:
                self.display.add_pane(p.name, p.display_name, p.avatar)
        budget = self.config.debate.token_budget_per_persona.opening
        tasks = [
            self._run_persona(
                p,
                OPENING_PROMPT.format(question=question),
                max_tokens=budget,
                round_no=1,
                state=state,
            )
            for p in personas
        ]
        await asyncio.gather(*tasks)

    async def _round2(
        self, personas: list[Persona], question: str, state: SessionState
    ) -> None:
        round1_summary = self._format_round(state.round(1))
        if self.display:
            self.display.set_header("Round 2/4 - Reaction Round")
            self.display.reset_panes()
        budget = self.config.debate.token_budget_per_persona.reaction
        for p in personas:
            if self.display:
                self.display.add_pane(p.name, p.display_name, p.avatar)
            template = (
                DEVILS_REACTION_PROMPT if p.name == "devils-advocate" else REACTION_PROMPT
            )
            await self._run_persona(
                p,
                template.format(question=question, round1_summary=round1_summary),
                max_tokens=budget,
                round_no=2,
                state=state,
            )

    async def _round3(
        self, personas: list[Persona], question: str, state: SessionState
    ) -> None:
        transcript = self._format_transcript(state, include_round=2)
        if self.display:
            self.display.set_header("Round 3/4 - Final Position")
            self.display.reset_panes()
            for p in personas:
                self.display.add_pane(p.name, p.display_name, p.avatar)
        budget = self.config.debate.token_budget_per_persona.final
        tasks = [
            self._run_persona(
                p,
                FINAL_PROMPT.format(question=question, transcript=transcript),
                max_tokens=budget,
                round_no=3,
                state=state,
            )
            for p in personas
        ]
        await asyncio.gather(*tasks)

    async def _synthesis(
        self, moderator: Persona, question: str, state: SessionState
    ) -> None:
        transcript = self._format_transcript(state, include_round=3)
        if self.display:
            self.display.set_header("Round 4/4 - Moderator Synthese (SCQA)")
            self.display.reset_panes()
            self.display.add_pane(
                moderator.name, moderator.display_name, moderator.avatar, style="cyan"
            )
        appender = self.display.appender(moderator.name) if self.display else None
        result = await self.client.converse(
            system=self._system_for(moderator),
            user_message=SYNTHESIS_PROMPT.format(question=question, transcript=transcript),
            max_tokens=self.config.debate.moderator_synthesis_tokens,
            rag=None,
            on_text=appender,
        )
        state.synthesis = result.text.strip()

    async def _check_convergence(self, moderator: Persona, state: SessionState) -> None:
        round2_summary = self._format_round(state.round(2))
        result = await self.client.converse(
            system=self._system_for(moderator),
            user_message=CONVERGENCE_PROMPT.format(round2_summary=round2_summary),
            max_tokens=150,
            rag=None,
            on_text=None,
        )
        parsed = _parse_convergence_json(result.text)
        state.convergence = parsed
        if parsed.converged and self.on_convergence:
            should_skip = await self.on_convergence(parsed.personas)
            state.r3_skipped = bool(should_skip)

    async def _run_persona(
        self,
        persona: Persona,
        user_message: str,
        *,
        max_tokens: int,
        round_no: int,
        state: SessionState,
    ) -> None:
        appender = self.display.appender(persona.name) if self.display else None
        result = await self.client.converse(
            system=self._system_for(persona),
            user_message=user_message,
            max_tokens=max_tokens,
            rag=self.rag,
            on_text=appender,
        )
        if self.display and appender and result.text and not _was_streamed(result):
            self.display.set_full_text(persona.name, result.text)
        state.contributions.append(
            PersonaContribution(
                persona=persona.name,
                display_name=persona.display_name,
                round_no=round_no,
                text=result.text.strip(),
                used_paths=list(result.used_paths),
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
            )
        )

    def _format_round(self, contributions: list[PersonaContribution]) -> str:
        parts = []
        for c in contributions:
            parts.append(f"### {c.display_name}\n{c.text}")
        return "\n\n".join(parts)

    def _format_transcript(self, state: SessionState, *, include_round: int) -> str:
        parts = []
        if state.moderator_opening:
            parts.append(f"## Moderator Opening\n{state.moderator_opening}")
        for r in range(1, include_round + 1):
            label = {1: "Opening Statements", 2: "Reaction Round", 3: "Final Position"}[r]
            block = self._format_round(state.round(r))
            if block:
                parts.append(f"## Round {r} - {label}\n{block}")
        return "\n\n".join(parts)


def _was_streamed(result) -> bool:
    # Heuristic: if the result has any text, the appender already received it via deltas.
    # Kept as a hook for future fallback handling.
    return True


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_convergence_json(text: str) -> ConvergenceResult:
    m = _JSON_RE.search(text)
    if not m:
        return ConvergenceResult(converged=False)
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return ConvergenceResult(converged=False)
    return ConvergenceResult(
        converged=bool(data.get("converged", False)),
        personas=[str(p) for p in (data.get("personas") or [])],
    )
