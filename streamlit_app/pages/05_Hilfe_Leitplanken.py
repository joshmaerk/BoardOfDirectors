import streamlit as st
from components.state import init_session_state

init_session_state()

st.title("🛡️ Hilfe & Leitplanken")
st.markdown(
    "Hier erfahren Sie, wie das Sicherheitssystem funktioniert und welche Eingaben zulässig sind."
)

st.divider()
st.subheader("Ampelsystem: Green / Yellow / Red")

col1, col2, col3 = st.columns(3)

with col1:
    st.success("✅ **Grün**")
    st.markdown(
        "Ihre Eingabe enthält keine sensiblen Muster. "
        "Das Sparring kann ohne Einschränkung gestartet werden."
    )

with col2:
    st.warning("⚠️ **Gelb**")
    st.markdown(
        "Interne, strategische oder budgetbezogene Begriffe erkannt. "
        "Sie müssen die Eingabe ausdrücklich bestätigen, bevor das Sparring startet."
    )

with col3:
    st.error("🚫 **Rot**")
    st.markdown(
        "Personenbezogene oder regulatorisch sensible Daten erkannt (z. B. IBAN, E-Mail, Kundennummer). "
        "Das Sparring wird **blockiert**. Überarbeiten Sie Ihre Eingabe."
    )

st.divider()
st.subheader("✅ Erlaubte Eingaben – Beispiele")

st.markdown(
    """
| Beispieleingabe | Einstufung |
|---|---|
| „Wie verbessern wir die cross-funktionale Zusammenarbeit?" | 🟢 Grün |
| „Welche Kommunikationsstrategie empfehlt sich für den Launch?" | 🟢 Grün |
| „Wie strukturieren wir das Onboarding-Programm für neue Mitarbeitende?" | 🟢 Grün |
| „Unsere interne Strategie sieht Wachstum in drei Märkten vor." | 🟡 Gelb – Bestätigung nötig |
| „Das Budget für das Projekt beträgt 200.000 €." | 🟡 Gelb – Bestätigung nötig |
"""
)

st.divider()
st.subheader("🚫 Nicht erlaubte Eingaben – Beispiele")

st.markdown(
    """
| Beispieleingabe | Einstufung | Grund |
|---|---|---|
| „Überweisen Sie auf DE89 3704 0044 0532 0130 00." | 🔴 Rot | IBAN erkannt |
| „Kontaktieren Sie max.mustermann@beispiel.de." | 🔴 Rot | E-Mail erkannt |
| „Kundennummer: 12345678" | 🔴 Rot | Kundendaten erkannt |
| „Kontonummer 987654321 bitte prüfen." | 🔴 Rot | Kontonummer erkannt |
| „Sozialversicherungsnummer: 65 070577 M 001" | 🔴 Rot | Personendaten erkannt |
"""
)

st.info(
    "**Hinweis:** Alle Beispiele auf dieser Seite sind synthetisch und enthalten keine echten Personendaten."
)

st.divider()
st.subheader("Häufige Fragen")

with st.expander("Was passiert mit meiner Eingabe?"):
    st.markdown(
        "Ihre Eingabe wird lokal im Browser klassifiziert. "
        "Im Mock-Modus verlässt sie das System nicht. "
        "Im Backend-Modus wird der Prompt an den konfigurierten Backend-Dienst übermittelt."
    )

with st.expander("Kann ich eine rote Einstufung umgehen?"):
    st.markdown(
        "Nein. Rote Einstufungen blockieren den Start des Sparrings. "
        "Bitte überarbeiten Sie Ihre Eingabe und entfernen Sie die sensiblen Inhalte."
    )

with st.expander("Was ist der Unterschied zwischen Gelb und Rot?"):
    st.markdown(
        "**Gelb** bedeutet, dass möglicherweise interne Informationen enthalten sind, "
        "die Sie bewusst eingeben möchten. Nach Ihrer Bestätigung kann das Sparring starten.\n\n"
        "**Rot** bedeutet, dass personenbezogene oder regulatorisch sensible Daten erkannt wurden. "
        "Dieses Muster lässt keinen Fortschritt zu."
    )
