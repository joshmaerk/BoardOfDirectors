from dataclasses import dataclass


@dataclass(frozen=True)
class UseCaseTemplate:
    key: str
    title: str
    description: str
    recommended_board: str
    recommended_output: str
    context_fields: tuple[str, ...]


@dataclass(frozen=True)
class BoardTemplate:
    key: str
    title: str
    description: str
    directors: tuple[str, ...]


@dataclass(frozen=True)
class OutputFormatTemplate:
    key: str
    title: str
    description: str
    sections: tuple[str, ...]


_USE_CASES: dict[str, UseCaseTemplate] = {
    "decision_brief": UseCaseTemplate(
        key="decision_brief",
        title="Entscheidungsvorlage",
        description="Strukturieren Sie eine Entscheidungsvorlage für Ihr Team oder den Vorstand.",
        recommended_board="management_board",
        recommended_output="decision_brief",
        context_fields=("Ziel der Entscheidung", "Optionen", "Empfehlung", "Risiken"),
    ),
    "communication_review": UseCaseTemplate(
        key="communication_review",
        title="Kommunikationsreview",
        description="Prüfen Sie Botschaften, Präsentationen oder Stakeholder-Kommunikation.",
        recommended_board="communication_board",
        recommended_output="communication_draft",
        context_fields=("Zielgruppe", "Kernbotschaft", "Medium", "Anlass"),
    ),
    "project_structuring": UseCaseTemplate(
        key="project_structuring",
        title="Projektstrukturierung",
        description="Erarbeiten Sie Struktur, Scope und Vorgehen für ein Projekt.",
        recommended_board="project_delivery_board",
        recommended_output="project_brief",
        context_fields=("Projektziel", "Scope", "Stakeholder", "Zeitrahmen"),
    ),
    "risk_challenge": UseCaseTemplate(
        key="risk_challenge",
        title="Risikoherausforderung",
        description="Fordern Sie Ihre Risikoeinschätzung mit kritischen Gegenperspektiven heraus.",
        recommended_board="banking_governance_board",
        recommended_output="risk_log",
        context_fields=("Risikobeschreibung", "Bewertung", "Gegenmaßnahmen", "Restrisiko"),
    ),
    "strategy_sparring": UseCaseTemplate(
        key="strategy_sparring",
        title="Strategie-Sparring",
        description="Testen Sie Ihre Strategie gegen erfahrene Kritiker und Berater.",
        recommended_board="management_board",
        recommended_output="executive_summary",
        context_fields=("Strategische Frage", "Ausgangssituation", "Hypothese", "Zeithorizont"),
    ),
    "concept_challenge": UseCaseTemplate(
        key="concept_challenge",
        title="Konzeptchallenge",
        description="Lassen Sie ein neues Konzept oder eine Idee kritisch prüfen.",
        recommended_board="learning_board",
        recommended_output="one_pager",
        context_fields=("Konzeptidee", "Ziel", "Zielgruppe", "Offene Fragen"),
    ),
}

_BOARD_TEMPLATES: dict[str, BoardTemplate] = {
    "management_board": BoardTemplate(
        key="management_board",
        title="Management Board",
        description="Strategische Perspektiven aus Unternehmensführung und Beratung.",
        directors=("Stratege", "CFO-Skeptiker", "Devil's Advocate", "Moderator"),
    ),
    "banking_governance_board": BoardTemplate(
        key="banking_governance_board",
        title="Banking Governance Board",
        description="Aufsichtsrechtliche und bankfachliche Perspektiven.",
        directors=("Banking Veteran", "CFO-Skeptiker", "Devil's Advocate", "Moderator"),
    ),
    "communication_board": BoardTemplate(
        key="communication_board",
        title="Communications Board",
        description="Fokus auf Stakeholder-Kommunikation und Tonalität.",
        directors=("Comms Coach", "Stratege", "Devil's Advocate", "Moderator"),
    ),
    "project_delivery_board": BoardTemplate(
        key="project_delivery_board",
        title="Project Delivery Board",
        description="Umsetzungsorientierte Perspektiven mit Fokus auf Planung und Risiko.",
        directors=("Stratege", "CFO-Skeptiker", "Banking Veteran", "Moderator"),
    ),
    "learning_board": BoardTemplate(
        key="learning_board",
        title="Learning Board",
        description="Offene, exploratorische Runde zum Prüfen neuer Ideen und Konzepte.",
        directors=("Stratege", "Devil's Advocate", "Comms Coach", "Moderator"),
    ),
}

_OUTPUT_FORMATS: dict[str, OutputFormatTemplate] = {
    "executive_summary": OutputFormatTemplate(
        key="executive_summary",
        title="Executive Summary",
        description="Kompakte Zusammenfassung für Entscheider.",
        sections=("Ausgangslage", "Kernaussagen", "Empfehlung"),
    ),
    "decision_brief": OutputFormatTemplate(
        key="decision_brief",
        title="Decision Brief",
        description="Strukturierte Entscheidungsvorlage mit Optionen und Empfehlung.",
        sections=("Entscheidungsfrage", "Optionen", "Bewertung", "Empfehlung", "Nächste Schritte"),
    ),
    "project_brief": OutputFormatTemplate(
        key="project_brief",
        title="Project Brief",
        description="Projektsteckbrief mit Zielen, Scope und Planung.",
        sections=("Ziel", "Scope", "Stakeholder", "Meilensteine", "Risiken"),
    ),
    "communication_draft": OutputFormatTemplate(
        key="communication_draft",
        title="Communication Draft",
        description="Kommunikationsentwurf mit Kernbotschaften und Tonempfehlung.",
        sections=("Zielgruppe", "Kernbotschaft", "Argumentation", "Tonalität", "Call-to-Action"),
    ),
    "risk_log": OutputFormatTemplate(
        key="risk_log",
        title="Risk Log",
        description="Strukturiertes Risikoprotokoll mit Bewertung und Maßnahmen.",
        sections=(
            "Risikobeschreibung",
            "Eintrittswahrscheinlichkeit",
            "Auswirkung",
            "Gegenmaßnahmen",
        ),
    ),
    "todo_plan": OutputFormatTemplate(
        key="todo_plan",
        title="To-Do-Plan",
        description="Priorisierte Aufgabenliste mit Verantwortlichkeiten.",
        sections=("Priorität", "Aufgabe", "Verantwortlich", "Frist"),
    ),
    "one_pager": OutputFormatTemplate(
        key="one_pager",
        title="One Pager",
        description="Einseitige Zusammenfassung eines Konzepts oder einer Idee.",
        sections=("Idee", "Nutzen", "Umsetzung", "Offene Punkte"),
    ),
}


def get_use_case_templates() -> dict[str, UseCaseTemplate]:
    return _USE_CASES


def get_board_templates() -> dict[str, BoardTemplate]:
    return _BOARD_TEMPLATES


def get_output_format_templates() -> dict[str, OutputFormatTemplate]:
    return _OUTPUT_FORMATS


def validate_template_references() -> list[str]:
    errors: list[str] = []
    boards = _BOARD_TEMPLATES.keys()
    outputs = _OUTPUT_FORMATS.keys()
    for uc in _USE_CASES.values():
        if uc.recommended_board not in boards:
            errors.append(
                f"UseCase '{uc.key}': recommended_board '{uc.recommended_board}' not found"
            )
        if uc.recommended_output not in outputs:
            errors.append(
                f"UseCase '{uc.key}': recommended_output '{uc.recommended_output}' not found"
            )
    return errors
