import streamlit as st


def get_access_token() -> str | None:
    """Return bearer token from session state, or None in mock/dev mode."""
    return st.session_state.get("entra_access_token") or None
