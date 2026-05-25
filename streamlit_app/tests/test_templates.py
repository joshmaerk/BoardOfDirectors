from components.templates import (
    get_board_templates,
    get_output_format_templates,
    get_use_case_templates,
    validate_template_references,
)

REQUIRED_USE_CASES = {
    "decision_brief",
    "communication_review",
    "project_structuring",
    "risk_challenge",
    "strategy_sparring",
    "concept_challenge",
}

REQUIRED_BOARDS = {
    "management_board",
    "banking_governance_board",
    "communication_board",
    "project_delivery_board",
    "learning_board",
}

REQUIRED_OUTPUTS = {
    "executive_summary",
    "decision_brief",
    "project_brief",
    "communication_draft",
    "risk_log",
    "todo_plan",
    "one_pager",
}


def test_all_required_use_cases_present():
    keys = set(get_use_case_templates().keys())
    assert REQUIRED_USE_CASES <= keys


def test_all_required_boards_present():
    keys = set(get_board_templates().keys())
    assert REQUIRED_BOARDS <= keys


def test_all_required_output_formats_present():
    keys = set(get_output_format_templates().keys())
    assert REQUIRED_OUTPUTS <= keys


def test_validate_template_references_returns_empty():
    errors = validate_template_references()
    assert errors == [], f"Template reference errors: {errors}"


def test_use_case_has_recommended_board():
    templates = get_use_case_templates()
    boards = get_board_templates()
    for uc in templates.values():
        assert uc.recommended_board in boards, f"{uc.key} has invalid recommended_board"


def test_use_case_has_recommended_output():
    templates = get_use_case_templates()
    outputs = get_output_format_templates()
    for uc in templates.values():
        assert uc.recommended_output in outputs, f"{uc.key} has invalid recommended_output"


def test_use_case_has_context_fields():
    for uc in get_use_case_templates().values():
        assert len(uc.context_fields) > 0, f"{uc.key} has no context_fields"


def test_board_has_directors():
    for board in get_board_templates().values():
        assert len(board.directors) > 0, f"{board.key} has no directors"
