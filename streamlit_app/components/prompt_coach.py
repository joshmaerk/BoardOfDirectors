from dataclasses import dataclass

from components.templates import get_output_format_templates, get_use_case_templates


@dataclass(frozen=True)
class PromptDraft:
    prompt: str
    quality_hints: list[str]
    missing_context_questions: list[str]


def build_prompt(
    use_case_key: str,
    context: dict[str, str],
    output_format_key: str,
) -> PromptDraft:
    use_cases = get_use_case_templates()
    output_formats = get_output_format_templates()

    uc = use_cases.get(use_case_key)
    fmt = output_formats.get(output_format_key)

    quality_hints: list[str] = []
    missing_questions: list[str] = []

    goal = context.get("goal", "").strip()
    if not goal:
        quality_hints.append("Formulieren Sie eine konkrete Frage oder ein klares Ziel.")
        missing_questions.append("Was genau möchten Sie mit diesem Sparring erreichen?")
    elif len(goal) < 15:
        quality_hints.append("Ihre Frage ist sehr kurz – mehr Kontext verbessert die Ergebnisse.")

    if uc:
        for field in uc.context_fields:
            value = context.get(field, "").strip()
            if not value:
                missing_questions.append(f"Fehlender Kontext: {field}")
            elif len(value) < 10:
                quality_hints.append(f"Feld '{field}' ist sehr kurz – bitte ergänzen Sie Details.")

    lines: list[str] = []

    uc_title = uc.title if uc else use_case_key
    lines.append(f"## Use Case: {uc_title}")
    lines.append("")

    if goal:
        lines.append(f"**Meine Frage / mein Ziel:**\n{goal}")
    else:
        lines.append("**Meine Frage / mein Ziel:** (bitte ergänzen)")
    lines.append("")

    if uc:
        context_section = []
        for field in uc.context_fields:
            value = context.get(field, "").strip()
            context_section.append(f"- {field}: {value if value else '(nicht angegeben)'}")
        if context_section:
            lines.append("**Kontext:**")
            lines.extend(context_section)
            lines.append("")

    if fmt:
        lines.append(f"**Erwartetes Ausgabeformat: {fmt.title}**")
        lines.append("Bitte strukturieren Sie Ihre Antwort in folgende Abschnitte:")
        for section in fmt.sections:
            lines.append(f"- {section}")
        lines.append("")

    lines.append("Bitte analysieren Sie die Fragestellung aus Ihrer Perspektive und geben Sie eine fundierte, kritische Einschätzung.")

    return PromptDraft(
        prompt="\n".join(lines),
        quality_hints=quality_hints,
        missing_context_questions=missing_questions,
    )
