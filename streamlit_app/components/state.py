import streamlit as st
from components.api_client import is_mock_mode

DEFAULT_STATE: dict = {
    "wizard_step": 1,
    "selected_use_case": None,
    "context_values": {},
    "safety_assessment": None,
    "yellow_confirmed": False,
    "prompt_draft": None,
    "selected_board": None,
    "selected_output_format": None,
    "current_run": None,
    "run_messages": [],
    "mock_mode": True,
    "session_runs": [],
}


def init_session_state() -> None:
    for key, default in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = default
    st.session_state["mock_mode"] = is_mock_mode()


def reset_wizard() -> None:
    wizard_keys = [
        "wizard_step",
        "selected_use_case",
        "context_values",
        "safety_assessment",
        "yellow_confirmed",
        "prompt_draft",
        "selected_board",
        "selected_output_format",
        "current_run",
        "run_messages",
    ]
    for key in wizard_keys:
        st.session_state[key] = DEFAULT_STATE[key]
