import streamlit as st
from components.api_client import BoardApiError, get_api_client, is_mock_mode
from components.prompt_coach import build_prompt
from components.renderers import build_markdown_export
from components.safety import assess_safety
from components.state import init_session_state, reset_wizard
from components.templates import (
    get_board_templates,
    get_output_format_templates,
    get_use_case_templates,
)

init_session_state()

st.title("🗣️ Neues Sparring")

if is_mock_mode():
    st.info(
        "ℹ️ **Mock-Modus aktiv** – kein Backend konfiguriert. Ergebnisse sind synthetische Beispiele."
    )

col_reset, _ = st.columns([1, 5])
with col_reset:
    if st.button("↺ Neu starten"):
        reset_wizard()
        st.rerun()

step = st.session_state["wizard_step"]

progress_labels = ["Use Case", "Kontext", "Safety", "Prompt", "Board & Format", "Ergebnis"]
st.progress(
    (step - 1) / len(progress_labels),
    text=f"Schritt {step} von {len(progress_labels)}: {progress_labels[step - 1]}",
)

st.divider()

# ---------------------------------------------------------------------------
# Schritt 1: Use-Case-Auswahl
# ---------------------------------------------------------------------------
if step == 1:
    st.subheader("1️⃣ Use Case auswählen")
    use_cases = get_use_case_templates()

    options = {uc.key: f"{uc.title} – {uc.description}" for uc in use_cases.values()}
    current = st.session_state.get("selected_use_case") or next(iter(use_cases.keys()))

    selected_key = st.radio(
        "Wählen Sie den passenden Use Case:",
        options=list(options.keys()),
        format_func=lambda k: options[k],
        index=list(options.keys()).index(current) if current in options else 0,
    )

    if st.button("Weiter →", key="step1_next"):
        st.session_state["selected_use_case"] = selected_key
        uc = use_cases[selected_key]
        st.session_state["selected_board"] = uc.recommended_board
        st.session_state["selected_output_format"] = uc.recommended_output
        st.session_state["wizard_step"] = 2
        st.rerun()

# ---------------------------------------------------------------------------
# Schritt 2: Kontext-Eingabe
# ---------------------------------------------------------------------------
elif step == 2:
    st.subheader("2️⃣ Kontext eingeben")
    use_cases = get_use_case_templates()
    uc = use_cases.get(st.session_state["selected_use_case"])

    st.markdown(f"**Use Case:** {uc.title if uc else '–'}")

    ctx = dict(st.session_state.get("context_values") or {})

    goal = st.text_area(
        "Ihre Frage oder Ihr Ziel *",
        value=ctx.get("goal", ""),
        placeholder="Was möchten Sie mit diesem Sparring erreichen?",
        height=100,
    )
    ctx["goal"] = goal

    if uc:
        for field in uc.context_fields:
            ctx[field] = st.text_input(
                field,
                value=ctx.get(field, ""),
                placeholder=f"{field} (optional, aber hilfreich)",
            )

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Zurück"):
            st.session_state["wizard_step"] = 1
            st.rerun()
    with col_next:
        if st.button("Weiter →", key="step2_next"):
            if not ctx.get("goal", "").strip():
                st.error("Bitte geben Sie mindestens eine Frage oder ein Ziel ein.")
            else:
                st.session_state["context_values"] = ctx
                assessment = assess_safety(" ".join(ctx.values()))
                st.session_state["safety_assessment"] = {
                    "level": assessment.level,
                    "reasons": assessment.reasons,
                    "recommendations": assessment.recommendations,
                    "can_continue": assessment.can_continue,
                }
                st.session_state["wizard_step"] = 3
                st.rerun()

# ---------------------------------------------------------------------------
# Schritt 3: Safety Assessment
# ---------------------------------------------------------------------------
elif step == 3:
    st.subheader("3️⃣ Sicherheitsprüfung")
    assessment = st.session_state.get("safety_assessment") or {}
    level = assessment.get("level", "green")
    reasons = assessment.get("reasons", [])
    recommendations = assessment.get("recommendations", [])
    can_continue = assessment.get("can_continue", True)

    if level == "green":
        st.success("✅ **Grün** – Keine sensiblen Inhalte erkannt.")
    elif level == "yellow":
        st.warning("⚠️ **Gelb** – Interne oder strategische Begriffe erkannt.")
    else:
        st.error("🚫 **Rot** – Sensible Daten erkannt. Bitte überarbeiten Sie Ihre Eingabe.")

    for r in reasons:
        st.markdown(f"- {r}")
    for rec in recommendations:
        st.info(f"💡 {rec}")

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Zurück"):
            st.session_state["wizard_step"] = 2
            st.rerun()

    if not can_continue:
        st.stop()

    with col_next:
        confirmed = True
        if level == "yellow":
            confirmed = st.checkbox(
                "Ich bestätige, dass ich keine vertraulichen Daten eingegeben habe und mit dem Risiko einverstanden bin."
            )
        if st.button("Weiter →", key="step3_next"):
            if level == "yellow" and not confirmed:
                st.error("Bitte bestätigen Sie die Sicherheitshinweise.")
            else:
                ctx = st.session_state.get("context_values") or {}
                draft = build_prompt(
                    use_case_key=st.session_state["selected_use_case"],
                    context=ctx,
                    output_format_key=st.session_state["selected_output_format"],
                )
                st.session_state["prompt_draft"] = {
                    "prompt": draft.prompt,
                    "quality_hints": draft.quality_hints,
                    "missing_context_questions": draft.missing_context_questions,
                }
                st.session_state["wizard_step"] = 4
                st.rerun()

# ---------------------------------------------------------------------------
# Schritt 4: Prompt Coach Review
# ---------------------------------------------------------------------------
elif step == 4:
    st.subheader("4️⃣ Prompt überprüfen und anpassen")
    draft = st.session_state.get("prompt_draft") or {}

    hints = draft.get("quality_hints", [])
    questions = draft.get("missing_context_questions", [])

    if hints:
        st.warning("**Hinweise zur Qualitätsverbesserung:**\n" + "\n".join(f"- {h}" for h in hints))
    if questions:
        with st.expander("Fehlende Kontextinformationen"):
            for q in questions:
                st.markdown(f"- {q}")

    edited_prompt = st.text_area(
        "Prompt (bearbeitbar)",
        value=draft.get("prompt", ""),
        height=300,
    )

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Zurück"):
            st.session_state["wizard_step"] = 3
            st.rerun()
    with col_next:
        if st.button("Weiter →", key="step4_next"):
            if st.session_state.get("prompt_draft"):
                st.session_state["prompt_draft"]["prompt"] = edited_prompt
            st.session_state["wizard_step"] = 5
            st.rerun()

# ---------------------------------------------------------------------------
# Schritt 5: Board & Output-Format
# ---------------------------------------------------------------------------
elif step == 5:
    st.subheader("5️⃣ Board und Ausgabeformat bestätigen")
    boards = get_board_templates()
    formats = get_output_format_templates()

    selected_board = st.selectbox(
        "Board",
        options=list(boards.keys()),
        format_func=lambda k: boards[k].title,
        index=list(boards.keys()).index(
            st.session_state.get("selected_board", next(iter(boards.keys())))
        )
        if st.session_state.get("selected_board") in boards
        else 0,
    )
    if selected_board in boards:
        st.caption(boards[selected_board].description)
        st.caption("Directors: " + ", ".join(boards[selected_board].directors))

    selected_format = st.selectbox(
        "Ausgabeformat",
        options=list(formats.keys()),
        format_func=lambda k: formats[k].title,
        index=list(formats.keys()).index(
            st.session_state.get("selected_output_format", next(iter(formats.keys())))
        )
        if st.session_state.get("selected_output_format") in formats
        else 0,
    )
    if selected_format in formats:
        st.caption(formats[selected_format].description)

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Zurück"):
            st.session_state["wizard_step"] = 4
            st.rerun()
    with col_next:
        if st.button("🚀 Sparring starten", key="step5_next"):
            st.session_state["selected_board"] = selected_board
            st.session_state["selected_output_format"] = selected_format
            st.session_state["wizard_step"] = 6
            st.rerun()

# ---------------------------------------------------------------------------
# Schritt 6: Ausführung & Ergebnis
# ---------------------------------------------------------------------------
elif step == 6:
    st.subheader("6️⃣ Ergebnis")

    current_run = st.session_state.get("current_run")
    run_messages = st.session_state.get("run_messages", [])

    if current_run is None:
        client = get_api_client()
        prompt = (st.session_state.get("prompt_draft") or {}).get("prompt", "")
        try:
            run = client.start_run(
                board_id=st.session_state.get("selected_board", "management_board"),
                question=prompt,
            )
            st.session_state["current_run"] = run

            with st.spinner("Board of Directors tagt …"):
                messages = []
                for msg in client.stream_messages(run["id"]):
                    messages.append(msg)
                    st.session_state["run_messages"] = messages

            finished = client.get_run(run["id"])
        except BoardApiError as e:
            st.error(f"❌ Fehler bei der Ausführung: {e}")
            if st.button("← Zurück zu Schritt 5"):
                st.session_state["wizard_step"] = 5
                st.session_state["current_run"] = None
                st.rerun()
            st.stop()

        st.session_state["current_run"] = finished
        current_run = finished

        session_runs = st.session_state.get("session_runs", [])
        session_runs.append(finished)
        st.session_state["session_runs"] = session_runs
        st.rerun()

    synthesis = current_run.get("synthesis", "")
    messages = current_run.get("messages", run_messages)

    if synthesis:
        st.success("**Synthese des Moderators:**")
        st.markdown(synthesis)
        st.divider()

    for msg in messages:
        role = msg.get("role", "Unbekannt")
        round_nr = msg.get("round", "")
        content = msg.get("content", "")
        with st.expander(
            f"🎙️ {role}" + (f" (Runde {round_nr})" if round_nr else ""), expanded=False
        ):
            st.markdown(content)

    st.divider()

    boards = get_board_templates()
    formats = get_output_format_templates()
    use_cases = get_use_case_templates()
    uc = use_cases.get(st.session_state.get("selected_use_case", ""), None)
    board = boards.get(st.session_state.get("selected_board", ""), None)
    fmt = formats.get(st.session_state.get("selected_output_format", ""), None)
    safety = st.session_state.get("safety_assessment") or {}

    md = build_markdown_export(
        question=(st.session_state.get("context_values") or {}).get("goal", ""),
        use_case_title=uc.title if uc else "",
        safety_level=safety.get("level", "green"),
        board_title=board.title if board else "",
        output_format_title=fmt.title if fmt else "",
        synthesis=synthesis,
        director_messages=messages,
    )

    st.download_button(
        label="📥 Ergebnis als Markdown herunterladen",
        data=md,
        file_name="board_of_directors_ergebnis.md",
        mime="text/markdown",
    )

    if st.button("🔄 Neues Sparring starten"):
        reset_wizard()
        st.rerun()
