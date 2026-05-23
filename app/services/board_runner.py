from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import SessionLocal
from app.core.logging import get_logger
from app.models import (
    Board,
    BoardMode,
    Director,
    DirectorMessage,
    MessageRole,
    Run,
    RunStatus,
)
from app.services.llm.base import ChatMessage, LLMClient, LLMResponse

log = get_logger(__name__)


class BoardRunner:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def execute(
        self,
        run_id: uuid.UUID,
        *,
        mode_override: BoardMode | None = None,
        rounds_override: int | None = None,
    ) -> None:
        async with SessionLocal() as session:
            board, run, directors = await self._load(session, run_id)
            if board is None or run is None:
                log.error("run_load_failed", run_id=str(run_id))
                return

            effective_mode = mode_override or board.mode
            effective_rounds = rounds_override or board.rounds

            try:
                # Honor a cancel that arrived before we started.
                if run.status == RunStatus.CANCELLED:
                    return

                run.status = RunStatus.RUNNING
                run.started_at = datetime.now(UTC)
                await session.commit()

                if effective_mode == BoardMode.PARALLEL:
                    director_outputs = await self._run_parallel(session, run, board, directors)
                elif effective_mode == BoardMode.SEQUENTIAL:
                    director_outputs = await self._run_sequential(session, run, board, directors)
                else:
                    director_outputs = await self._run_discussion(
                        session, run, board, directors, rounds=effective_rounds
                    )

                if await self._is_cancelled(session, run):
                    return

                synthesis = await self._maybe_synthesize(session, run, board, director_outputs)
                run.result_summary = synthesis or self._fallback_summary(director_outputs)
                run.status = RunStatus.DONE
            except Exception as exc:
                log.exception("run_failed", run_id=str(run_id))
                run.status = RunStatus.FAILED
                run.error = str(exc)
            finally:
                run.finished_at = datetime.now(UTC)
                await session.commit()

    async def _load(
        self, session: AsyncSession, run_id: uuid.UUID
    ) -> tuple[Board | None, Run | None, list[Director]]:
        run = await session.get(Run, run_id)
        if run is None:
            return None, None, []
        board = await session.scalar(
            select(Board).options(selectinload(Board.members)).where(Board.id == run.board_id)
        )
        if board is None:
            return None, run, []
        director_ids = [m.director_id for m in board.members]
        if not director_ids:
            return board, run, []
        directors_result = await session.scalars(
            select(Director).where(Director.id.in_(director_ids))
        )
        by_id = {d.id: d for d in directors_result}
        ordered = [
            by_id[m.director_id]
            for m in sorted(board.members, key=lambda m: m.position)
            if m.director_id in by_id
        ]
        return board, run, ordered

    @staticmethod
    async def _is_cancelled(session: AsyncSession, run: Run) -> bool:
        # Re-read the status column from the DB so a concurrent /cancel call
        # that flipped the row is visible. Returning True lets the caller bail
        # out of the run without overwriting `status`.
        await session.refresh(run, attribute_names=["status"])
        return run.status == RunStatus.CANCELLED

    async def _run_parallel(
        self,
        session: AsyncSession,
        run: Run,
        board: Board,
        directors: list[Director],
    ) -> list[tuple[Director, str]]:
        async def call(director: Director) -> tuple[Director, LLMResponse]:
            prompt_override = self._override_for(board, director.id)
            messages = [
                ChatMessage(role="system", content=prompt_override or director.system_prompt),
                ChatMessage(role="user", content=run.input),
            ]
            response = await self._llm.chat(
                model=director.model,
                messages=messages,
                temperature=director.temperature,
            )
            return director, response

        results = await asyncio.gather(*(call(d) for d in directors))
        outputs: list[tuple[Director, str]] = []
        for director, response in results:
            await self._persist_message(
                session, run, director, response, round_=0, role=MessageRole.DIRECTOR
            )
            outputs.append((director, response.content))
        await session.commit()
        return outputs

    async def _run_sequential(
        self,
        session: AsyncSession,
        run: Run,
        board: Board,
        directors: list[Director],
    ) -> list[tuple[Director, str]]:
        outputs: list[tuple[Director, str]] = []
        running_context = run.input
        for director in directors:
            prompt_override = self._override_for(board, director.id)
            messages = [
                ChatMessage(role="system", content=prompt_override or director.system_prompt),
                ChatMessage(role="user", content=running_context),
            ]
            response = await self._llm.chat(
                model=director.model,
                messages=messages,
                temperature=director.temperature,
            )
            await self._persist_message(
                session, run, director, response, round_=0, role=MessageRole.DIRECTOR
            )
            outputs.append((director, response.content))
            running_context = (
                f"Previous director ({director.role}) said:\n{response.content}\n\n"
                f"Original question:\n{run.input}"
            )
        await session.commit()
        return outputs

    async def _run_discussion(
        self,
        session: AsyncSession,
        run: Run,
        board: Board,
        directors: list[Director],
        *,
        rounds: int,
    ) -> list[tuple[Director, str]]:
        history: list[tuple[Director, str]] = []
        for round_idx in range(rounds):
            transcript = self._format_transcript(history) if history else ""

            async def call(
                director: Director, _transcript: str = transcript
            ) -> tuple[Director, LLMResponse]:
                prompt_override = self._override_for(board, director.id)
                user_content = (
                    f"Question: {run.input}\n\nDiscussion so far:\n{_transcript}"
                    if _transcript
                    else run.input
                )
                messages = [
                    ChatMessage(
                        role="system",
                        content=prompt_override or director.system_prompt,
                    ),
                    ChatMessage(role="user", content=user_content),
                ]
                response = await self._llm.chat(
                    model=director.model,
                    messages=messages,
                    temperature=director.temperature,
                )
                return director, response

            results = await asyncio.gather(*(call(d) for d in directors))
            for director, response in results:
                await self._persist_message(
                    session,
                    run,
                    director,
                    response,
                    round_=round_idx,
                    role=MessageRole.DIRECTOR,
                )
                history.append((director, response.content))
            await session.commit()

        return [(d, c) for d, c in history[-len(directors) :]] if directors else []

    async def _maybe_synthesize(
        self,
        session: AsyncSession,
        run: Run,
        board: Board,
        outputs: list[tuple[Director, str]],
    ) -> str | None:
        if board.synthesis_director_id is None or not outputs:
            return None
        chair = await session.get(Director, board.synthesis_director_id)
        if chair is None:
            return None
        transcript = self._format_transcript(outputs)
        messages = [
            ChatMessage(role="system", content=chair.system_prompt),
            ChatMessage(
                role="user",
                content=(
                    f"Question: {run.input}\n\n"
                    f"Director responses:\n{transcript}\n\n"
                    "Synthesize a final answer reflecting the board's input."
                ),
            ),
        ]
        response = await self._llm.chat(
            model=chair.model,
            messages=messages,
            temperature=chair.temperature,
        )
        await self._persist_message(
            session, run, chair, response, round_=99, role=MessageRole.SYNTHESIS
        )
        await session.commit()
        return response.content

    async def _persist_message(
        self,
        session: AsyncSession,
        run: Run,
        director: Director,
        response: LLMResponse,
        *,
        round_: int,
        role: MessageRole,
    ) -> None:
        msg = DirectorMessage(
            run_id=run.id,
            director_id=director.id,
            round=round_,
            role=role,
            content=response.content,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            latency_ms=response.latency_ms,
        )
        session.add(msg)
        run.total_tokens += response.prompt_tokens + response.completion_tokens

    @staticmethod
    def _override_for(board: Board, director_id: uuid.UUID) -> str | None:
        for member in board.members:
            if member.director_id == director_id:
                return member.prompt_override
        return None

    @staticmethod
    def _format_transcript(items: list[tuple[Director, str]]) -> str:
        return "\n\n".join(f"[{d.name} — {d.role}]\n{content}" for d, content in items)

    @staticmethod
    def _fallback_summary(outputs: list[tuple[Director, str]]) -> str:
        if not outputs:
            return "(no directors responded)"
        return BoardRunner._format_transcript(outputs)
