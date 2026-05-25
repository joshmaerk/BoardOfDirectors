import os
import time
from collections.abc import Generator

_ROLE_LABELS = {"synthesis": "Moderator", "director": "Direktor"}


def _role_label(role: str) -> str:
    return _ROLE_LABELS.get(role, role or "Unbekannt")


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

    def list_runs(self) -> list[dict]:
        return [
            {
                "id": "mock_run_001",
                "status": "done",
                "question": "Wie können wir unsere Strategie schärfen?",
                "synthesis": _MOCK_MESSAGES[-1]["content"],
                "messages": _MOCK_MESSAGES[:-1],
                "error": None,
            },
            {
                "id": "mock_run_002",
                "status": "done",
                "question": "Welche Risiken übersehen wir bei unserem Ansatz?",
                "synthesis": "**Synthese:** Das Board empfiehlt eine systematische Risikoanalyse mit drei Szenarien.",
                "messages": [],
                "error": None,
            },
        ]

    def cancel_run(self, run_id: str) -> None:
        pass


class BoardApiClient:
    from typing import ClassVar

    _ERROR_MAP: ClassVar[dict[int, str]] = {
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

    def _get(self, path: str) -> dict | list:
        import requests

        try:
            resp = requests.get(f"{self.base_url}{path}", headers=self._headers(), timeout=15)
        except requests.RequestException as exc:
            raise BoardApiError(f"Netzwerkfehler: {exc}") from exc
        if not resp.ok:
            self._raise_for_status(resp.status_code, resp.text)
        return resp.json()

    def _post(self, path: str, payload: dict) -> dict:
        import requests

        try:
            resp = requests.post(
                f"{self.base_url}{path}", json=payload, headers=self._headers(), timeout=15
            )
        except requests.RequestException as exc:
            raise BoardApiError(f"Netzwerkfehler: {exc}") from exc
        if not resp.ok:
            self._raise_for_status(resp.status_code, resp.text)
        return resp.json()

    def list_directors(self) -> list[dict]:
        result = self._get("/api/v1/directors")
        return result if isinstance(result, list) else []

    def list_boards(self) -> list[dict]:
        result = self._get("/api/v1/boards")
        return result if isinstance(result, list) else []

    def start_run(self, board_id: str, question: str, **overrides) -> dict:
        payload = {"input": question, **overrides}
        data = self._post(f"/api/v1/boards/{board_id}/runs", payload)
        return {
            "id": str(data.get("id", "")),
            "status": data.get("status", "pending"),
            "question": question,
            "synthesis": "",
            "messages": [],
            "error": None,
        }

    def get_run(self, run_id: str) -> dict:
        data = self._get(f"/api/v1/runs/{run_id}")
        messages_raw = self._get(f"/api/v1/runs/{run_id}/messages")
        messages = [
            {
                "role": m.get("persona_name") or _role_label(m.get("role", "")),
                "round": m.get("round", ""),
                "content": m.get("content", ""),
            }
            for m in (messages_raw if isinstance(messages_raw, list) else [])
        ]
        return {
            "id": str(data.get("id", run_id)),
            "status": data.get("status", "unknown"),
            "question": data.get("input", ""),
            "synthesis": data.get("result_summary") or "",
            "messages": messages,
            "error": data.get("error"),
        }

    def stream_messages(self, run_id: str) -> Generator[dict, None, None]:
        import requests

        try:
            resp = requests.get(
                f"{self.base_url}/api/v1/runs/{run_id}/stream",
                headers={**self._headers(), "Accept": "text/event-stream"},
                stream=True,
                timeout=120,
            )
        except requests.RequestException as exc:
            raise BoardApiError(f"Netzwerkfehler beim Streaming: {exc}") from exc

        if not resp.ok:
            self._raise_for_status(resp.status_code)

        import json

        current_event = "message"
        for raw_line in resp.iter_lines():
            if not raw_line:
                current_event = "message"
                continue
            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
            if line.startswith("event:"):
                current_event = line[6:].strip()
                continue
            if not line.startswith("data:"):
                continue
            payload_str = line[5:].strip()
            if not payload_str:
                continue
            if payload_str == "[DONE]":
                break
            if current_event == "error":
                raise BoardApiError(f"Stream-Fehler: {payload_str}")
            if current_event == "status":
                break
            try:
                event = json.loads(payload_str)
                yield {
                    "role": event.get("persona_name") or _role_label(event.get("role", "")),
                    "round": event.get("round", ""),
                    "content": event.get("content", ""),
                }
            except json.JSONDecodeError:
                continue

    def list_runs(self) -> list[dict]:
        result = self._get("/api/v1/runs")
        return [
            {
                "id": str(r.get("id", "")),
                "status": r.get("status", "unknown"),
                "question": r.get("input", ""),
                "synthesis": r.get("result_summary") or "",
                "messages": [],
                "error": r.get("error"),
            }
            for r in (result if isinstance(result, list) else [])
        ]

    def cancel_run(self, run_id: str) -> None:
        self._post(f"/api/v1/runs/{run_id}/cancel", {})


def get_api_client(access_token: str | None = None) -> MockBoardApiClient | BoardApiClient:
    base_url = os.environ.get("BOARD_API_BASE_URL", "").strip()
    if base_url:
        return BoardApiClient(base_url=base_url, access_token=access_token)
    return MockBoardApiClient()


def is_mock_mode() -> bool:
    return not os.environ.get("BOARD_API_BASE_URL", "").strip()
