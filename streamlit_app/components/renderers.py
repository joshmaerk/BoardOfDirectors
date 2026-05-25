def build_markdown_export(
    question: str,
    use_case_title: str,
    safety_level: str,
    board_title: str,
    output_format_title: str,
    synthesis: str,
    director_messages: list[dict],
) -> str:
    safety_labels = {"green": "Grün ✅", "yellow": "Gelb ⚠️", "red": "Rot 🚫"}
    safety_label = safety_labels.get(safety_level, safety_level)

    lines: list[str] = [
        "# Board of Directors Ergebnis",
        "",
        "## Fragestellung",
        "",
        question or "(keine Fragestellung)",
        "",
        "## Use Case",
        "",
        use_case_title or "(kein Use Case)",
        "",
        "## Safety Einstufung",
        "",
        safety_label,
        "",
        "## Board",
        "",
        board_title or "(kein Board)",
        "",
        "## Output Format",
        "",
        output_format_title or "(kein Format)",
        "",
        "## Synthese",
        "",
        synthesis or "(keine Synthese verfügbar)",
        "",
        "## Director-Beitraege",
        "",
    ]

    if director_messages:
        for msg in director_messages:
            role = msg.get("role", "Unbekannt")
            round_nr = msg.get("round", "")
            content = msg.get("content", "")
            round_label = f" (Runde {round_nr})" if round_nr else ""
            lines.append(f"### {role}{round_label}")
            lines.append("")
            lines.append(content)
            lines.append("")
    else:
        lines.append("(Keine Director-Beiträge vorhanden)")
        lines.append("")

    return "\n".join(lines)
