"""Tests for the RoundtableDisplay multi-pane state machine.

These tests exercise the data-model side of the display (pane registration,
text accumulation, header/footer state) without driving the rich Live loop.
"""

from __future__ import annotations

from rich.console import Console

from conductor.client import TokenLedger
from conductor.streaming import PaneState, RoundtableDisplay


def _display() -> RoundtableDisplay:
    return RoundtableDisplay(
        console=Console(record=True, force_terminal=False),
        ledger=TokenLedger(budget_total=1_000, output=200),
    )


def test_add_pane_registers_pane_with_text_placeholder():
    disp = _display()
    disp.add_pane("stratege", "Der Stratege", "S")
    assert "stratege" in disp.panes
    assert isinstance(disp.panes["stratege"], PaneState)
    assert disp.panes["stratege"].text == ""


def test_appender_returns_callable_that_grows_pane_text():
    disp = _display()
    disp.add_pane("stratege", "Der Stratege", "S")
    append = disp.appender("stratege")
    append("Hallo ")
    append("Welt")
    assert disp.panes["stratege"].text == "Hallo Welt"


def test_appender_for_unknown_pane_is_noop():
    disp = _display()
    append = disp.appender("ghost")
    append("noise")
    assert "ghost" not in disp.panes


def test_set_full_text_overwrites_pane_text():
    disp = _display()
    disp.add_pane("stratege", "Der Stratege", "S")
    disp.appender("stratege")("partial")
    disp.set_full_text("stratege", "final")
    assert disp.panes["stratege"].text == "final"


def test_set_header_updates_header_field():
    disp = _display()
    disp.set_header("Round 1/4 - Opening")
    assert disp.header == "Round 1/4 - Opening"


def test_reset_panes_clears_all_panes_but_keeps_header():
    disp = _display()
    disp.set_header("X")
    disp.add_pane("a", "A", "a")
    disp.add_pane("b", "B", "b")
    disp.reset_panes()
    assert disp.panes == {}
    assert disp.header == "X"


def test_footer_text_reflects_ledger_status():
    disp = _display()
    rendered = disp._footer_text()
    assert "200/1000" in rendered
    assert "grün" in rendered or "gelb" in rendered or "rot" in rendered


def test_footer_empty_when_no_ledger():
    disp = RoundtableDisplay()
    assert disp._footer_text() == ""


def test_render_produces_rich_group_with_header_and_pane():
    disp = _display()
    disp.set_header("Round 1")
    disp.add_pane("stratege", "Der Stratege", "S")
    disp.appender("stratege")("Statement.")
    group = disp._render()
    # We only check the renderable type and that it contains at least 2 items
    # (header panel + persona panel + footer panel).
    assert len(group.renderables) >= 3


def test_context_manager_open_and_close_safely():
    disp = _display()
    with disp:
        disp.add_pane("a", "A", "a")
        disp.appender("a")("text")
    assert disp._live is None
