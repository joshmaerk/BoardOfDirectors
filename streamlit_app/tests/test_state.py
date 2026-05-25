from components.state import DEFAULT_STATE, init_session_state, reset_wizard

WIZARD_KEYS = [
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


def test_init_session_state_sets_all_keys(mock_st_session):
    init_session_state()
    for key in DEFAULT_STATE:
        assert key in mock_st_session, f"Key '{key}' not set by init_session_state"


def test_init_session_state_does_not_overwrite_existing(mock_st_session):
    mock_st_session["wizard_step"] = 99
    init_session_state()
    assert mock_st_session["wizard_step"] == 99


def test_reset_wizard_restores_defaults(mock_st_session):
    init_session_state()
    mock_st_session["wizard_step"] = 5
    mock_st_session["selected_use_case"] = "strategy_sparring"
    mock_st_session["context_values"] = {"goal": "test"}
    reset_wizard()
    for key in WIZARD_KEYS:
        assert mock_st_session[key] == DEFAULT_STATE[key], f"Key '{key}' not reset"


def test_reset_wizard_leaves_session_runs_intact(mock_st_session):
    init_session_state()
    mock_st_session["session_runs"] = [{"id": "run_1"}]
    reset_wizard()
    assert mock_st_session["session_runs"] == [{"id": "run_1"}]
