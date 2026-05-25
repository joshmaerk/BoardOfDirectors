import streamlit as st
from components.state import init_session_state
from components.templates import get_board_templates, get_use_case_templates

init_session_state()

st.title("📚 Board-Bibliothek")
st.markdown("Überblick über alle verfügbaren Boards und Use Cases.")

st.divider()
st.subheader("🏛️ Board-Templates")

boards = get_board_templates()
for board in boards.values():
    with st.expander(f"**{board.title}**"):
        st.markdown(board.description)
        st.markdown("**Directors:** " + " · ".join(board.directors))

st.divider()
st.subheader("🎯 Use Cases")

use_cases = get_use_case_templates()
boards_map = get_board_templates()

for uc in use_cases.values():
    with st.expander(f"**{uc.title}**"):
        st.markdown(uc.description)
        rec_board = boards_map.get(uc.recommended_board)
        st.markdown(
            f"**Empfohlenes Board:** {rec_board.title if rec_board else uc.recommended_board}"
        )
        st.markdown("**Hilfreiche Kontextfelder:** " + " · ".join(uc.context_fields))
        if st.button("Sparring starten", key=f"lib_start_{uc.key}"):
            st.session_state["selected_use_case"] = uc.key
            st.session_state["selected_board"] = uc.recommended_board
            st.session_state["selected_output_format"] = uc.recommended_output
            st.session_state["wizard_step"] = 1
            st.switch_page("pages/02_Neues_Sparring.py")
