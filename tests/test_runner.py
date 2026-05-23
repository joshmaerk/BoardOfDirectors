from __future__ import annotations

import pytest

from app.models import (
    Board,
    BoardDirector,
    BoardMode,
    Director,
    MessageRole,
    Run,
    RunStatus,
    Visibility,
)
from app.services import board_runner as board_runner_module
from app.services.board_runner import BoardRunner

pytestmark = pytest.mark.asyncio


async def _seed_board(session_factory, *, mode: BoardMode, rounds: int = 1, synth: bool = False):
    async with session_factory() as session:
        d1 = Director(
            owner_id="user-a",
            name="CFO",
            role="CFO",
            system_prompt="You are CFO.",
            model="gpt-4o-mini",
            temperature=0.3,
            visibility=Visibility.PRIVATE,
        )
        d2 = Director(
            owner_id="user-a",
            name="CTO",
            role="CTO",
            system_prompt="You are CTO.",
            model="gpt-4o-mini",
            temperature=0.3,
            visibility=Visibility.PRIVATE,
        )
        chair = None
        if synth:
            chair = Director(
                owner_id="user-a",
                name="CEO",
                role="CEO",
                system_prompt="You are the chair. Synthesize.",
                model="gpt-4o-mini",
                temperature=0.2,
                visibility=Visibility.PRIVATE,
            )
            session.add(chair)
        session.add_all([d1, d2])
        await session.flush()

        board = Board(
            owner_id="user-a",
            name="Exec",
            mode=mode,
            rounds=rounds,
            synthesis_director_id=chair.id if chair else None,
            visibility=Visibility.PRIVATE,
        )
        board.members = [
            BoardDirector(director_id=d1.id, position=0),
            BoardDirector(director_id=d2.id, position=1),
        ]
        session.add(board)
        await session.flush()

        run = Run(
            owner_id="user-a",
            board_id=board.id,
            input="Should we ship?",
            status=RunStatus.PENDING,
        )
        session.add(run)
        await session.commit()
        return run.id, board.id


@pytest.fixture
def patched_session_local(session_factory):
    original = board_runner_module.SessionLocal
    board_runner_module.SessionLocal = session_factory
    try:
        yield
    finally:
        board_runner_module.SessionLocal = original


async def _fetch_run(session_factory, run_id):
    from sqlalchemy import select

    from app.models import DirectorMessage

    async with session_factory() as session:
        run = await session.get(Run, run_id)
        messages = list(
            await session.scalars(
                select(DirectorMessage)
                .where(DirectorMessage.run_id == run_id)
                .order_by(DirectorMessage.created_at)
            )
        )
        return run, messages


async def test_parallel_mode_runs_each_director_once(
    session_factory, fake_llm, patched_session_local
):
    run_id, _ = await _seed_board(session_factory, mode=BoardMode.PARALLEL)

    await BoardRunner(fake_llm).execute(run_id)

    run, messages = await _fetch_run(session_factory, run_id)
    assert run.status == RunStatus.DONE
    assert run.finished_at is not None
    assert len(messages) == 2
    assert {m.role for m in messages} == {MessageRole.DIRECTOR}
    assert run.total_tokens > 0
    assert run.result_summary is not None


async def test_sequential_mode_runs_each_director_once_in_order(
    session_factory, fake_llm, patched_session_local
):
    run_id, _ = await _seed_board(session_factory, mode=BoardMode.SEQUENTIAL)

    await BoardRunner(fake_llm).execute(run_id)

    run, messages = await _fetch_run(session_factory, run_id)
    assert run.status == RunStatus.DONE
    assert len(messages) == 2
    # Second director must have seen the first director's output in its input
    second_user_msg = fake_llm.calls[1][1][-1].content
    assert "Previous director" in second_user_msg


async def test_discussion_mode_produces_message_per_round(
    session_factory, fake_llm, patched_session_local
):
    run_id, _ = await _seed_board(
        session_factory, mode=BoardMode.DISCUSSION, rounds=3
    )

    await BoardRunner(fake_llm).execute(run_id)

    run, messages = await _fetch_run(session_factory, run_id)
    assert run.status == RunStatus.DONE
    assert len(messages) == 2 * 3
    rounds = {m.round for m in messages}
    assert rounds == {0, 1, 2}


async def test_synthesis_director_emits_final_message(
    session_factory, fake_llm, patched_session_local
):
    run_id, _ = await _seed_board(
        session_factory, mode=BoardMode.PARALLEL, synth=True
    )

    await BoardRunner(fake_llm).execute(run_id)

    run, messages = await _fetch_run(session_factory, run_id)
    assert run.status == RunStatus.DONE
    synthesis = [m for m in messages if m.role == MessageRole.SYNTHESIS]
    assert len(synthesis) == 1
    assert run.result_summary == synthesis[0].content


async def test_failing_llm_marks_run_failed(
    session_factory, patched_session_local
):
    class BrokenLLM:
        async def chat(self, **_kwargs):
            raise RuntimeError("boom")

    run_id, _ = await _seed_board(session_factory, mode=BoardMode.PARALLEL)

    await BoardRunner(BrokenLLM()).execute(run_id)

    run, _ = await _fetch_run(session_factory, run_id)
    assert run.status == RunStatus.FAILED
    assert run.error and "boom" in run.error
