import streamlit as st

from components.state import init_session_state

st.set_page_config(
    page_title="Board of Directors",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()

st.title("Board of Directors")
st.markdown(
    "Nutzen Sie das Navigationsmenü links, um ein neues Sparring zu starten "
    "oder Ihre bisherigen Runs einzusehen."
)
