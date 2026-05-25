import re
from dataclasses import dataclass, field

_IBAN_PATTERN = re.compile(r"\bDE\d{2}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{2}\b", re.IGNORECASE)
_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")

_RED_KEYWORDS = [
    "kundennummer",
    "kontonummer",
    "sozialversicherung",
    "steuernummer",
    "personalausweis",
    "reisepassnummer",
    "kreditkartennummer",
]

_YELLOW_KEYWORDS = [
    "strategie",
    "budget",
    "intern",
    "vertraulich",
    "umsatz",
    "gewinn",
    "marge",
    "ebitda",
    "prognose",
    "planung",
    "geheimhaltung",
]


@dataclass(frozen=True)
class SafetyAssessment:
    level: str
    reasons: list[str]
    recommendations: list[str]
    can_continue: bool


def contains_iban(text: str) -> bool:
    return bool(_IBAN_PATTERN.search(text))


def contains_email(text: str) -> bool:
    return bool(_EMAIL_PATTERN.search(text))


def contains_red_keywords(text: str) -> list[str]:
    lower = text.lower()
    return [kw for kw in _RED_KEYWORDS if kw in lower]


def contains_yellow_keywords(text: str) -> list[str]:
    lower = text.lower()
    return [kw for kw in _YELLOW_KEYWORDS if kw in lower]


def assess_safety(text: str) -> SafetyAssessment:
    reasons: list[str] = []
    recommendations: list[str] = []

    if contains_iban(text):
        reasons.append("IBAN-ähnliche Zeichenfolge erkannt.")
        recommendations.append("Entfernen Sie Bankverbindungsdaten aus Ihrer Eingabe.")
        return SafetyAssessment(level="red", reasons=reasons, recommendations=recommendations, can_continue=False)

    if contains_email(text):
        reasons.append("E-Mail-Adresse erkannt.")
        recommendations.append("Entfernen Sie personenbezogene Kontaktdaten aus Ihrer Eingabe.")
        return SafetyAssessment(level="red", reasons=reasons, recommendations=recommendations, can_continue=False)

    red_kws = contains_red_keywords(text)
    if red_kws:
        reasons.append(f"Sensible Begriffe erkannt: {', '.join(red_kws)}.")
        recommendations.append("Entfernen Sie Kundendaten oder persönliche Kennziffern.")
        return SafetyAssessment(level="red", reasons=reasons, recommendations=recommendations, can_continue=False)

    yellow_kws = contains_yellow_keywords(text)
    if yellow_kws:
        reasons.append(f"Interne oder strategische Begriffe erkannt: {', '.join(yellow_kws)}.")
        recommendations.append("Stellen Sie sicher, dass Sie keine vertraulichen Zahlen oder Pläne eingeben.")
        return SafetyAssessment(level="yellow", reasons=reasons, recommendations=recommendations, can_continue=True)

    return SafetyAssessment(
        level="green",
        reasons=["Keine sensiblen Muster erkannt."],
        recommendations=[],
        can_continue=True,
    )
