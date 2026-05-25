import pytest
from components.safety import (
    SafetyAssessment,
    assess_safety,
    contains_email,
    contains_iban,
    contains_red_keywords,
    contains_yellow_keywords,
)


def test_green_harmless_question():
    result = assess_safety("Wie sollte ich die Teamkommunikation verbessern?")
    assert result.level == "green"
    assert result.can_continue is True


def test_green_returns_safety_assessment_type():
    result = assess_safety("Welche Strategie empfehlen Sie für das Onboarding neuer Mitglieder?")
    assert isinstance(result, SafetyAssessment)


def test_yellow_strategy_term():
    result = assess_safety("Unsere interne Strategie sieht vor, den Umsatz zu steigern.")
    assert result.level == "yellow"
    assert result.can_continue is True
    assert len(result.reasons) > 0


def test_yellow_budget_term():
    result = assess_safety("Das Budget für Q3 beträgt etwa 500.000 Euro.")
    assert result.level == "yellow"
    assert result.can_continue is True


def test_red_iban():
    result = assess_safety("Bitte überweisen Sie auf DE89 3704 0044 0532 0130 00.")
    assert result.level == "red"
    assert result.can_continue is False


def test_red_email():
    result = assess_safety("Schreiben Sie an max.mustermann@beispiel.de für Details.")
    assert result.level == "red"
    assert result.can_continue is False


def test_red_keyword_kundennummer():
    result = assess_safety("Die Kundennummer lautet 12345678.")
    assert result.level == "red"
    assert result.can_continue is False


def test_red_keyword_kontonummer():
    result = assess_safety("Kontonummer: 987654321")
    assert result.level == "red"
    assert result.can_continue is False


def test_contains_iban_true():
    assert contains_iban("DE89 3704 0044 0532 0130 00") is True


def test_contains_iban_false():
    assert contains_iban("Kein Konto vorhanden") is False


def test_contains_email_true():
    assert contains_email("kontakt@beispiel.de") is True


def test_contains_email_false():
    assert contains_email("Keine E-Mail hier") is False


def test_contains_red_keywords_found():
    found = contains_red_keywords("Bitte die Kundennummer prüfen")
    assert "kundennummer" in found


def test_contains_red_keywords_empty():
    assert contains_red_keywords("Harmloser Text") == []


def test_contains_yellow_keywords_found():
    found = contains_yellow_keywords("Das Budget und der Umsatz")
    assert "budget" in found
    assert "umsatz" in found


def test_contains_yellow_keywords_empty():
    assert contains_yellow_keywords("Kein heikler Begriff") == []


def test_red_takes_priority_over_yellow():
    result = assess_safety("Strategie: Kundennummer 123 intern nutzen")
    assert result.level == "red"
