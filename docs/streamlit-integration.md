# Streamlit ↔ Board of Directors API

How the legacy Streamlit app calls into this backend.

## Auth pattern (Token forwarding)

Streamlit already authenticates the user against Entra (Azure AD) via
`streamlit-oauth` / `msal-streamlit-authenticator`. After login, the **same
access token** is forwarded as `Authorization: Bearer …` on every API call.
The backend validates it against Entra JWKS, checks audience / tenant /
roles, and uses the `oid` claim as the stable user identity.

There is no separate API key, no service-to-service exchange.

## Configuration in Streamlit

```toml
# .streamlit/secrets.toml
[board_api]
base_url = "https://bod-api-prod.<region>.azurecontainerapps.io/api/v1"
# scope you request from Entra so the access token's `aud` matches the API:
scope    = "api://board-of-directors/.default"
```

## Minimal API client

```python
# board_api_client.py
from __future__ import annotations

import json
from typing import Any, Iterable

import httpx
import streamlit as st


class BoardClient:
    def __init__(self, base_url: str, access_token: str, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=timeout,
        )

    # --- directors / boards --------------------------------------------------

    def list_directors(self) -> list[dict]:
        return self._client.get("/directors").raise_for_status().json()

    def create_director(self, payload: dict) -> dict:
        return self._client.post("/directors", json=payload).raise_for_status().json()

    def create_board(self, payload: dict) -> dict:
        return self._client.post("/boards", json=payload).raise_for_status().json()

    # --- runs ----------------------------------------------------------------

    def start_run(self, board_id: str, question: str, **overrides: Any) -> dict:
        return (
            self._client
            .post(f"/boards/{board_id}/runs", json={"input": question, **overrides})
            .raise_for_status()
            .json()
        )

    def get_run(self, run_id: str) -> dict:
        return self._client.get(f"/runs/{run_id}").raise_for_status().json()

    def stream_messages(self, run_id: str) -> Iterable[dict]:
        """Generator that yields each Director message as it arrives."""
        with httpx.stream(
            "GET",
            f"{self._base_url}/runs/{run_id}/stream",
            headers=self._client.headers,
            timeout=None,
        ) as resp:
            resp.raise_for_status()
            event = None
            for line in resp.iter_lines():
                if not line:
                    event = None
                    continue
                if line.startswith("event: "):
                    event = line[len("event: "):]
                elif line.startswith("data: "):
                    payload = json.loads(line[len("data: "):])
                    yield {"event": event, "data": payload}

    # --- account -------------------------------------------------------------

    def export_my_data(self) -> dict:
        return self._client.get("/me/export").raise_for_status().json()

    def delete_my_account(self) -> None:
        self._client.delete("/me").raise_for_status()


@st.cache_resource
def get_client() -> BoardClient:
    """Streamlit caches the client per-session; token is refreshed by the
    auth layer above."""
    base_url = st.secrets["board_api"]["base_url"]
    token = st.session_state["entra_access_token"]
    return BoardClient(base_url=base_url, access_token=token)
```

## Live-streaming the board's reactions

```python
client = get_client()
run = client.start_run(board_id="…", question="Wie sollte ich X angehen?")
st.write(f"Run id: `{run['id']}`")

placeholder = st.empty()
buffered: list[str] = []
for evt in client.stream_messages(run["id"]):
    if evt["event"] == "message":
        msg = evt["data"]
        buffered.append(f"**{msg['role']}** (Runde {msg['round']}): {msg['content']}")
        placeholder.markdown("\n\n---\n\n".join(buffered))
    elif evt["event"] == "status":
        status = evt["data"]
        if status["status"] == "done":
            st.success("Board fertig.")
        else:
            st.error(f"Run endete als {status['status']}: {status.get('error')}")
        break
```

## Sample director payloads

A round-table of GPT + Claude:

```python
client.create_director({
    "name": "CFO Skeptiker",
    "role": "CFO",
    "model": "gpt-4o-mini",
    "system_prompt": "Du bist konservativer CFO. Fordere Zahlen, Business Case, Risiken.",
    "temperature": 0.3,
})
client.create_director({
    "name": "Stratege",
    "role": "Strategy",
    "model": "claude-sonnet-4-5",
    "system_prompt": "Du bist McKinsey-Stratege. Optionen + Trade-offs, kein Storytelling.",
    "temperature": 0.6,
})
```

Then a board (the API verifies you own / have access to every director ID):

```python
client.create_board({
    "name": "Exec Roundtable",
    "mode": "discussion",
    "rounds": 3,
    "members": [
        {"director_id": cfo_id, "position": 0},
        {"director_id": strat_id, "position": 1},
    ],
    "synthesis_director_id": chair_id,   # optional: a 'CEO' that synthesises at the end
})
```

## Error handling

| Status | Meaning | Streamlit reaction |
|---|---|---|
| `401` | Token expired / wrong audience | Trigger re-login |
| `403` | Token missing required role (`board.user`) | Show "kein Zugriff" page |
| `404` | Resource not owned / soft-deleted | Refresh the list |
| `422` | Payload exceeds an input limit (system_prompt > 16 KB, etc.) | Show validation error inline |
| `429` | Rate limit (per-user) | Back off and surface "Bitte warte einen Moment" |
| `5xx` | API / provider hiccup | Toast + auto-retry the GET; do not auto-retry POSTs |

## Local development against a local API

If you `docker compose up` the backend with `AUTH_DEV_BYPASS=true`, **any
request is accepted** as a fixed dev user. Useful for UI iteration without
an Entra setup. Never enable this in prod (it is a dedicated env var, and
the API logs a warning on startup).
