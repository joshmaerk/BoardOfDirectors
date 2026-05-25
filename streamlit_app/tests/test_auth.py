from components.auth import get_access_token


def test_get_access_token_returns_none_when_not_set(mock_st_session):
    result = get_access_token()
    assert result is None


def test_get_access_token_returns_none_for_empty_string(mock_st_session):
    mock_st_session["entra_access_token"] = ""
    result = get_access_token()
    assert result is None


def test_get_access_token_returns_token_when_set(mock_st_session):
    mock_st_session["entra_access_token"] = "eyJhbGciOiJSUzI1NiJ9.test"
    result = get_access_token()
    assert result == "eyJhbGciOiJSUzI1NiJ9.test"
