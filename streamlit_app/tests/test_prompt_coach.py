from components.prompt_coach import PromptDraft, build_prompt


def test_prompt_contains_user_goal():
    draft = build_prompt(
        use_case_key="strategy_sparring",
        context={"goal": "Wie positionieren wir uns im Wettbewerb?"},
        output_format_key="executive_summary",
    )
    assert "Wie positionieren wir uns im Wettbewerb?" in draft.prompt


def test_empty_goal_produces_hint():
    draft = build_prompt(
        use_case_key="decision_brief",
        context={},
        output_format_key="decision_brief",
    )
    assert len(draft.quality_hints) > 0 or len(draft.missing_context_questions) > 0


def test_missing_context_produces_questions():
    draft = build_prompt(
        use_case_key="decision_brief",
        context={"goal": "Soll ich Option A oder B wählen?"},
        output_format_key="decision_brief",
    )
    assert len(draft.missing_context_questions) > 0


def test_prompt_not_empty():
    draft = build_prompt(
        use_case_key="risk_challenge",
        context={"goal": "Wie riskant ist unser Vorgehen?"},
        output_format_key="risk_log",
    )
    assert len(draft.prompt) > 0


def test_returns_prompt_draft_type():
    draft = build_prompt(
        use_case_key="concept_challenge",
        context={"goal": "Ist dieses Konzept tragfähig?", "Konzeptidee": "KI-gestützter Assistent"},
        output_format_key="one_pager",
    )
    assert isinstance(draft, PromptDraft)


def test_output_format_sections_in_prompt():
    draft = build_prompt(
        use_case_key="strategy_sparring",
        context={"goal": "Wie skalieren wir das Produkt?"},
        output_format_key="executive_summary",
    )
    assert "Ausgangslage" in draft.prompt
    assert "Empfehlung" in draft.prompt


def test_short_goal_produces_hint():
    draft = build_prompt(
        use_case_key="strategy_sparring",
        context={"goal": "Hilfe"},
        output_format_key="executive_summary",
    )
    assert any("kurz" in h.lower() for h in draft.quality_hints)
