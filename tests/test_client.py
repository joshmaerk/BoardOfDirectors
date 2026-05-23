"""Tests for the TokenLedger and budget-tracking primitives."""

from __future__ import annotations

import pytest

from conductor.client import BudgetExceededError, TokenLedger


def test_token_ledger_add_accumulates():
    ledger = TokenLedger(budget_total=1_000)
    ledger.add(50, 100)
    ledger.add(20, 30)
    assert ledger.input == 70
    assert ledger.output == 130


def test_token_ledger_status_green_below_70_percent():
    ledger = TokenLedger(budget_total=1_000, output=500)
    assert ledger.status == "grün"


def test_token_ledger_status_yellow_between_70_and_90_percent():
    ledger = TokenLedger(budget_total=1_000, output=800)
    assert ledger.status == "gelb"


def test_token_ledger_status_red_above_90_percent():
    ledger = TokenLedger(budget_total=1_000, output=950)
    assert ledger.status == "rot"


def test_token_ledger_utilization_with_zero_budget_returns_zero():
    ledger = TokenLedger(budget_total=0, output=42)
    assert ledger.utilization == 0.0


def test_token_ledger_check_raises_when_budget_exceeded():
    ledger = TokenLedger(budget_total=100, output=100)
    with pytest.raises(BudgetExceededError) as exc_info:
        ledger.check()
    assert "100/100" in str(exc_info.value)


def test_token_ledger_check_passes_when_under_budget():
    ledger = TokenLedger(budget_total=100, output=99)
    ledger.check()  # should not raise
