import os
import time
from typing import Generator


class BoardApiError(Exception):
    pass


_MOCK_DIRECTORS = [
    {"id": "stratege", "name": "Stratege", "role": "McKinsey/BCG-Strategie"},
    {"id": "cfo", "name": "CFO-Skeptiker", "role": "Konservativer Finanzvorstand"},
    {"id": "banking", "name": "Banking Veteran", "role": "30 Jahre ECB-supervised Banking"},
    {"id": "devil", "name": "Devil's Advocate", "role": "Strukturierter Querdenker"},
    {"id": "comms", "name": "Comms Coach", "role": "Stakeholder-Kommunikation"},
    {"id": "moderator", "name": "Moderator", "role": "Neutral, SCQA-Synthese"},
]

_MOCK_BOARDS = [
    {"id": "management_board", "name": "Management Board"},
    {"id": "banking_governance_board", "name": "Banking Governance Board"},
    {"id": "communication_board", "name": "Communications Board"},
    {"id": "project_delivery_board", "name": "Project Delivery Board"},
    {"id": "learning_board", "name": "Learning Board"},
]

_MOCK_MESSAGES = [
    {
        "role": "Stratege",
        "round": 1,
        "content": (
            "Aus strategischer Sicht sehe ich hier einen klaren Handlungsbedarf. "
            "Die Kernfrage ist, ob wir die richtige Priorität setzen. "
            "Ich empfehle, zunächst die Ausgangshypothese zu schärfen und dann in Szenarien zu denken."
        ),
    },
    {
        "role": "CFO-Skeptiker",
        "round": 1,
        "content": (
            "Die Zahlen überzeugen mich noch nicht. Welchen Business Case haben wir? "
            "Was kostet das, was bringt es, und was ist der Zeithorizont für den Break-even? "
            "Ohne klare Kennzahlen bleibt das Wunschdenken."
        ),
    },
    {
        "role": "Devil's Advocate",
        "round": 1,
        "content": (
            "Ich möchte den Konsens herausfordern: Was, wenn die Grundannahme falsch ist? "
            "Haben wir alternative Szenarien geprüft? "
            "Die blinden Flecken liegen oft dort, wo wir uns am sichersten fühlen."
        ),
    },
    {
        "role": "Moderator",
        "round": 2,
        "content": (
            "**Synthese:** Die Runde zeigt drei zentrale Spannungsfelder: "
            "strategische Priorisierung, wirtschaftliche Rechtfertigung und blinde Flecken im Ansatz. "
            "**Empfehlung:** Schärfen Sie die Hypothese, bauen Sie einen Minimal-Business-Case "
            "und validieren Sie Ihre Kernannahme mit einem Stakeholder-Interview."
        ),
    },
]


class MockBoardApiClient:
    def list_directors(self) -> list[dict]:
        return _MOCK_DIRECTORS

    def list_boards(self) -> list[dict]:
        return _MOCK_BOARDS

    def start_run(self, board_id: str, question: str, **overrides) -> dict:
        return {
            "id": "mock_run_001",
            "status": "running",
            "question": question,
            "board_id": board_id,
            "synthesis": "",
            "messages": [],
            "error": None,
        }

    def get_run(self, run_id: str) -> dict:
        return {
            "id": run_id,
            "status": "done",
            "question": "(Mock-Run)",
            "synthesis": _MOCK_MESSAGES[-1]["content"],
            "messages": _MOCK_MESSAGES[:-1],
            "error": None,
        }

    def stream_messages(self, run_id: str) -> Generator[dict, None, None]:
        for msg in _MOCK_MESSAGES:
            time.sleep(0.3)
            yield msg

    def cancel_run(self, run_id: str) -> None:
        pass


class BoardApiClient:
    """Real HTTP client – connected in Task 9."""

    _ERROR_MAP = {
        401: "Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.",
        403: "Sie haben keine Berechtigung für diese Aktion.",
        404: "Die angeforderte Ressource wurde nicht gefunden.",
        422: "Die Eingabe ist ungültig. Bitte prüfen Sie Ihre Angaben.",
        429: "Zu viele Anfragen. Bitte warten Sie einen Moment.",
    }

    def __init__(self, base_url: str, access_token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.access_token:
            h["Authorization"] = f"Bearer {self.access_token}"
        return h

    def _raise_for_status(self, status_code: int, detail: str = "") -> None:
        msg = self._ERROR_MAP.get(status_code)
        if msg is None:
            if status_code >= 500:
                msg = "Der Dienst ist vorübergehend nicht verfügbar. Bitte versuchen Sie es später erneut."
            else:
                msg = f"Unbekannter Fehler (HTTP {status_code}). {detail}".strip()
        raise BoardApiError(msg)

    def list_directors(self) -> list[dict]:
        raise NotImplementedError("Implemented in Task 9")

    def list_boards(self) -> list[dict]:
        raise NotImplementedError("Implemented in Task 9")

    def start_run(self, board_id: str, question: str, **overrides) -> dict:
        raise NotImplementedError("Implemented in Task 9")

    def get_run(self, run_id: str) -> dict:
        raise NotImplementedError("Implemented in Task 9")

    def stream_messages(self, run_id: str) -> Generator[dict, None, None]:
        raise NotImplementedError("Implemented in Task 9")
        yield  # make it a generator

    def cancel_run(self, run_id: str) -> None:
        raise NotImplementedError("Implemented in Task 9")


def get_api_client(access_token: str | None = None) -> MockBoardApiClient | BoardApiClient:
    base_url = os.environ.get("BOARD_API_BASE_URL", "").strip()
    if base_url:
        return BoardApiClient(base_url=base_url, access_token=access_token)
    return MockBoardApiClient()


def is_mock_mode() -> bool:
    return not os.environ.get("BOARD_API_BASE_URL", "").strip()
