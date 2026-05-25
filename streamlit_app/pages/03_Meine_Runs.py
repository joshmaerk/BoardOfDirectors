import streamlit as st
from components.api_client import BoardApiError, get_api_client, is_mock_mode
from components.state import init_session_state

init_session_state()

st.title("📋 Meine Runs")

session_runs = st.session_state.get("session_runs", [])
client = get_api_client()

if is_mock_mode():
    st.info("ℹ️ **Mock-Modus aktiv** – Runs werden nur für diese Sitzung gespeichert.")
    runs_to_show = list(reversed(session_runs))
else:
    try:
        backend_runs = client.list_runs()
        backend_ids = {r["id"] for r in backend_runs}
        extra = [r for r in reversed(session_runs) if r["id"] not in backend_ids]
        runs_to_show = backend_runs + extra
    except BoardApiError:
        st.warning("⚠️ Run-Verlauf konnte nicht geladen werden. Zeige Sitzungs-Runs.")
        runs_to_show = list(reversed(session_runs))

if not runs_to_show:
    st.markdown(
        "Noch keine Runs gefunden. "
        "Starten Sie ein [Neues Sparring](02_Neues_Sparring), um einen Run zu erstellen."
    )
else:
    label = "dieser Sitzung" if is_mock_mode() else "Ihrem Konto"
    st.markdown(f"**{len(runs_to_show)} Run(s) in {label}:**")
    for i, run in enumerate(runs_to_show, start=1):
        run_id = run.get("id", f"run_{i}")
        status = run.get("status", "–")
        question = run.get("question", "(keine Fragestellung)")
        synthesis = run.get("synthesis", "")

        _STATUS_ICONS = {
            "done": "✅",
            "running": "⏳",
            "failed": "❌",
            "cancelled": "🚫",
            "pending": "🕐",
        }
        icon = _STATUS_ICONS.get(status, "❓")

        with st.expander(
            f"{icon} Run {run_id} – {question[:60]}{'…' if len(question) > 60 else ''}"
        ):
            st.markdown(f"**Status:** {status}")
            st.markdown(f"**Frage:** {question}")
            if synthesis:
                st.markdown("**Synthese:**")
                st.markdown(synthesis)
            messages = run.get("messages", [])
            if messages:
                with st.expander("Director-Beiträge anzeigen"):
                    for msg in messages:
                        role = msg.get("role", "Unbekannt")
                        content = msg.get("content", "")
                        st.markdown(f"**{role}:** {content}")
