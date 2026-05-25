from components.renderers import build_markdown_export

_REQUIRED_SECTIONS = [
    "# Board of Directors Ergebnis",
    "## Fragestellung",
    "## Use Case",
    "## Safety Einstufung",
    "## Board",
    "## Output Format",
    "## Synthese",
    "## Director-Beitraege",
]


def _full_export(**kwargs) -> str:
    defaults: dict = {
        "question": "Wie verbessern wir die Teamkommunikation?",
        "use_case_title": "Kommunikationsreview",
        "safety_level": "green",
        "board_title": "Communications Board",
        "output_format_title": "Communication Draft",
        "synthesis": "Das Board empfiehlt regelmäßige Retrospektiven.",
        "director_messages": [
            {"role": "Stratege", "round": 1, "content": "Ich sehe Potenzial."},
            {"role": "CFO-Skeptiker", "round": 1, "content": "Die Kosten sind zu prüfen."},
        ],
    }
    defaults.update(kwargs)
    return build_markdown_export(**defaults)


def test_all_required_sections_present():
    md = _full_export()
    for section in _REQUIRED_SECTIONS:
        assert section in md, f"Missing section: {section}"


def test_question_in_output():
    md = _full_export(question="Welche Strategie ist richtig?")
    assert "Welche Strategie ist richtig?" in md


def test_director_messages_rendered():
    md = _full_export()
    assert "Stratege" in md
    assert "Ich sehe Potenzial." in md


def test_empty_director_messages_no_crash():
    md = _full_export(director_messages=[])
    assert "## Director-Beitraege" in md
    assert "Keine Director-Beiträge" in md


def test_safety_level_green_label():
    md = _full_export(safety_level="green")
    assert "Grün" in md


def test_safety_level_yellow_label():
    md = _full_export(safety_level="yellow")
    assert "Gelb" in md


def test_safety_level_red_label():
    md = _full_export(safety_level="red")
    assert "Rot" in md


def test_empty_synthesis_no_crash():
    md = _full_export(synthesis="")
    assert "## Synthese" in md


def test_output_is_deterministic():
    md1 = _full_export()
    md2 = _full_export()
    assert md1 == md2
