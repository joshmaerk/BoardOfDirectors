import streamlit as st

from components.api_client import is_mock_mode
from components.state import init_session_state

init_session_state()

st.title("📋 Meine Runs")

if is_mock_mode():
    st.info("ℹ️ **Mock-Modus aktiv** – Runs werden nur für diese Sitzung gespeichert.")

session_runs = st.session_state.get("session_runs", [])

if not session_runs:
    st.markdown(
        "Noch keine Runs in dieser Sitzung. "
        "Starten Sie ein [Neues Sparring](02_Neues_Sparring), um einen Run zu erstellen."
    )
else:
    st.markdown(f"**{len(session_runs)} Run(s) in dieser Sitzung:**")
    for i, run in enumerate(reversed(session_runs), start=1):
        run_id = run.get("id", f"run_{i}")
        status = run.get("status", "–")
        question = run.get("question", "(keine Fragestellung)")
        synthesis = run.get("synthesis", "")

        _STATUS_ICONS = {"done": "✅", "running": "⏳", "failed": "❌", "cancelled": "🚫", "pending": "🕐"}
        icon = _STATUS_ICONS.get(status, "❓")

        with st.expander(f"{icon} Run {run_id} – {question[:60]}{'…' if len(question) > 60 else ''}"):
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

if not is_mock_mode():
    st.divider()
    st.markdown("**Persistente Runs (Backend)**")
    st.info(
        "Der Backend-Endpunkt für eine vollständige Run-Liste ist in dieser Version noch nicht verfügbar. "
        "Nur Runs der aktuellen Sitzung werden angezeigt."
    )
