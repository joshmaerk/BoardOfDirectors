from unittest.mock import MagicMock, patch

import pytest
from components.api_client import (
    BoardApiClient,
    BoardApiError,
    MockBoardApiClient,
    get_api_client,
    is_mock_mode,
)

# ---------------------------------------------------------------------------
# MockBoardApiClient
# ---------------------------------------------------------------------------


def test_mock_list_directors_returns_six():
    client = MockBoardApiClient()
    directors = client.list_directors()
    assert len(directors) == 6


def test_mock_list_boards_returns_five():
    client = MockBoardApiClient()
    boards = client.list_boards()
    assert len(boards) == 5


def test_mock_start_run_returns_expected_shape():
    client = MockBoardApiClient()
    run = client.start_run("management_board", "Wie optimieren wir das Team?")
    assert run["id"] == "mock_run_001"
    assert run["status"] == "running"
    assert run["question"] == "Wie optimieren wir das Team?"


def test_mock_get_run_returns_done():
    client = MockBoardApiClient()
    run = client.get_run("mock_run_001")
    assert run["status"] == "done"
    assert run["synthesis"]  # non-empty string


def test_mock_stream_messages_yields_messages():
    client = MockBoardApiClient()
    # Patch sleep so test is fast
    with patch("time.sleep"):
        messages = list(client.stream_messages("mock_run_001"))
    assert len(messages) >= 1
    assert "role" in messages[0]
    assert "content" in messages[0]


def test_mock_cancel_run_does_not_raise():
    MockBoardApiClient().cancel_run("any_id")


# ---------------------------------------------------------------------------
# is_mock_mode / get_api_client factory
# ---------------------------------------------------------------------------


def test_is_mock_mode_true_without_env(monkeypatch):
    monkeypatch.delenv("BOARD_API_BASE_URL", raising=False)
    assert is_mock_mode() is True


def test_is_mock_mode_false_with_env(monkeypatch):
    monkeypatch.setenv("BOARD_API_BASE_URL", "http://localhost:8000")
    assert is_mock_mode() is False


def test_get_api_client_returns_mock_without_env(monkeypatch):
    monkeypatch.delenv("BOARD_API_BASE_URL", raising=False)
    assert isinstance(get_api_client(), MockBoardApiClient)


def test_get_api_client_returns_real_with_env(monkeypatch):
    monkeypatch.setenv("BOARD_API_BASE_URL", "http://localhost:8000")
    assert isinstance(get_api_client(), BoardApiClient)


# ---------------------------------------------------------------------------
# BoardApiClient – error mapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status_code, expected_fragment",
    [
        (401, "Sitzung"),
        (403, "Berechtigung"),
        (404, "nicht gefunden"),
        (422, "ungültig"),
        (429, "Anfragen"),
        (500, "nicht verfügbar"),
        (503, "nicht verfügbar"),
    ],
)
def test_raise_for_status_maps_codes(status_code, expected_fragment):
    client = BoardApiClient(base_url="http://example.com")
    with pytest.raises(BoardApiError, match=expected_fragment):
        client._raise_for_status(status_code)


def test_raise_for_status_unknown_code_includes_code():
    client = BoardApiClient(base_url="http://example.com")
    with pytest.raises(BoardApiError, match="418"):
        client._raise_for_status(418)


# ---------------------------------------------------------------------------
# BoardApiClient – headers
# ---------------------------------------------------------------------------


def test_headers_without_token():
    client = BoardApiClient(base_url="http://example.com")
    headers = client._headers()
    assert "Authorization" not in headers
    assert headers["Content-Type"] == "application/json"


def test_headers_with_token():
    client = BoardApiClient(base_url="http://example.com", access_token="tok_xyz")
    headers = client._headers()
    assert headers["Authorization"] == "Bearer tok_xyz"


# ---------------------------------------------------------------------------
# BoardApiClient – network error handling
# ---------------------------------------------------------------------------


def test_get_raises_board_api_error_on_network_failure():
    import requests as req_lib

    client = BoardApiClient(base_url="http://example.com")
    with patch("requests.get", side_effect=req_lib.RequestException("timeout")):
        with pytest.raises(BoardApiError, match="Netzwerkfehler"):
            client._get("/api/v1/boards")


def test_post_raises_board_api_error_on_network_failure():
    import requests as req_lib

    client = BoardApiClient(base_url="http://example.com")
    with patch("requests.post", side_effect=req_lib.RequestException("timeout")):
        with pytest.raises(BoardApiError, match="Netzwerkfehler"):
            client._post("/api/v1/runs", {})


def test_get_raises_on_http_error():
    client = BoardApiClient(base_url="http://example.com")
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 404
    mock_resp.text = "Not found"
    with patch("requests.get", return_value=mock_resp):
        with pytest.raises(BoardApiError, match="nicht gefunden"):
            client._get("/api/v1/boards/missing")
