import streamlit as st

from components.state import init_session_state

init_session_state()

st.title("🏛️ Board of Directors – Willkommen")

st.markdown(
    """
**Board of Directors** ist ein KI-gestütztes Sparring-System für interne Entscheider.
Strukturierte Perspektiven aus verschiedenen Rollen helfen Ihnen, Entscheidungen,
Strategien und Kommunikation zu schärfen.
"""
)

st.divider()

st.subheader("🛡️ Sicherheitshinweise")
st.info(
    "**Bitte geben Sie keine personenbezogenen oder vertraulichen Daten ein.**  \n"
    "Keine IBANs, E-Mail-Adressen, Kundennummern oder Kontonummern.  \n"
    "Strategische oder budgetbezogene Informationen werden zur Überprüfung markiert."
)

st.divider()

st.subheader("🚀 Womit möchten Sie starten?")

use_cases = [
    ("📋 Entscheidungsvorlage", "decision_brief", "Strukturieren Sie eine Entscheidungsvorlage für Ihr Team oder den Vorstand."),
    ("📣 Kommunikationsreview", "communication_review", "Prüfen Sie Botschaften, Präsentationen oder Stakeholder-Kommunikation."),
    ("🗂️ Projektstrukturierung", "project_structuring", "Erarbeiten Sie Struktur, Scope und Vorgehen für ein Projekt."),
    ("⚠️ Risikoherausforderung", "risk_challenge", "Fordern Sie Ihre Risikoeinschätzung mit kritischen Gegenperspektiven heraus."),
    ("🎯 Strategie-Sparring", "strategy_sparring", "Testen Sie Ihre Strategie gegen erfahrene Kritiker und Berater."),
    ("💡 Konzeptchallenge", "concept_challenge", "Lassen Sie ein neues Konzept oder eine Idee kritisch prüfen."),
]

cols = st.columns(3)
for i, (label, key, description) in enumerate(use_cases):
    with cols[i % 3]:
        st.markdown(f"**{label}**")
        st.caption(description)
        if st.button("Starten", key=f"start_{key}"):
            st.session_state["selected_use_case"] = key
            st.session_state["wizard_step"] = 1
            st.switch_page("pages/02_Neues_Sparring.py")

st.divider()

if st.session_state.get("mock_mode"):
    st.caption("ℹ️ Mock-Modus aktiv – kein Backend konfiguriert.")
