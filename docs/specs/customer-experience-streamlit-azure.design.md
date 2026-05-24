# Technical Design: Customer-Experience Streamlit Azure

Status: Draft  
Parent spec: `docs/specs/customer-experience-streamlit-azure.md`  
Requirements: `docs/specs/customer-experience-streamlit-azure.requirements.md`

---

## 1. Design intent

The WebUI makes the existing BoardOfDirectors capability usable for internal expert users with low AI maturity. The system reduces cognitive load by guiding users from use-case selection to structured prompt creation, safety classification, board execution and exportable work product.

The backend remains the orchestration authority. Streamlit is a thin, generic UI layer.

---

## 2. High-level architecture

```text
User
  |
  v
Streamlit WebUI
  |-- templates.py          static use cases, board templates, output formats
  |-- safety.py             local deterministic safety assessment
  |-- prompt_coach.py       local deterministic prompt construction
  |-- renderers.py          result rendering and Markdown export
  |-- api_client.py         FastAPI client and mock client
  |-- state.py              session-state helpers
  |
  v
FastAPI Backend
  |-- directors
  |-- boards
  |-- runs
  |-- run messages / SSE
```

MVP behavior:

- If `BOARD_API_BASE_URL` is missing, use mock mode.
- If `BOARD_API_BASE_URL` is present, use backend mode.
- Safety and prompt coach remain local for MVP.
- Optional backend endpoints for safety, prompt coach and feedback are future extensions.

---

## 3. Proposed file structure

```text
streamlit_app/
  app.py
  requirements.txt
  Dockerfile
  .streamlit/
    config.toml
  pages/
    01_Start.py
    02_Neues_Sparring.py
    03_Meine_Runs.py
    04_Board_Bibliothek.py
    05_Hilfe_Leitplanken.py
    06_Admin.py
  components/
    __init__.py
    api_client.py
    auth.py
    prompt_coach.py
    renderers.py
    safety.py
    state.py
    templates.py
  tests/
    test_prompt_coach.py
    test_renderers.py
    test_safety.py
    test_templates.py
```

Admin page is optional for MVP and may be omitted if role information is not available.

---

## 4. Module design

### 4.1 `streamlit_app/app.py`

Responsibility:

- Set Streamlit page config.
- Provide entrypoint.
- Initialize common session-state defaults.
- Keep the file thin and avoid business logic.

Expected call:

```python
from components.state import init_session_state

init_session_state()
```

### 4.2 `components/templates.py`

Responsibility:

- Define static use-case templates.
- Define static board templates.
- Define static output format templates.
- Provide helper functions for lookup and validation.

Suggested dataclasses:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class UseCaseTemplate:
    key: str
    title: str
    description: str
    recommended_board: str
    recommended_output: str
    context_fields: list[str]

@dataclass(frozen=True)
class BoardTemplate:
    key: str
    title: str
    description: str
    directors: list[str]

@dataclass(frozen=True)
class OutputFormatTemplate:
    key: str
    title: str
    description: str
    sections: list[str]
```

Required exports:

```python
def get_use_case_templates() -> dict[str, UseCaseTemplate]: ...
def get_board_templates() -> dict[str, BoardTemplate]: ...
def get_output_format_templates() -> dict[str, OutputFormatTemplate]: ...
def validate_template_references() -> list[str]: ...
```

Design rules:

- No Streamlit imports in this module.
- Pure Python only.
- All required templates from requirements must be present.

### 4.3 `components/safety.py`

Responsibility:

- Classify user input into `green`, `yellow`, or `red`.
- Provide reasons and recommendations.
- Detect common sensitive patterns.

Suggested dataclass:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SafetyAssessment:
    level: str
    reasons: list[str]
    recommendations: list[str]
    can_continue: bool
```

Required exports:

```python
def assess_safety(text: str) -> SafetyAssessment: ...
def contains_iban(text: str) -> bool: ...
def contains_email(text: str) -> bool: ...
def contains_red_keywords(text: str) -> list[str]: ...
def contains_yellow_keywords(text: str) -> list[str]: ...
```

Classification order:

1. Red pattern or red keyword returns `red`.
2. Else yellow keyword returns `yellow`.
3. Else return `green`.

Design rules:

- Deterministic and testable.
- No LLM call.
- No Streamlit imports.

### 4.4 `components/prompt_coach.py`

Responsibility:

- Build improved prompt draft from selected use case, context, output format and board.
- Generate quality hints.

Suggested dataclass:

```python
@dataclass(frozen=True)
class PromptDraft:
    prompt: str
    quality_hints: list[str]
    missing_context_questions: list[str]
```

Required export:

```python
def build_prompt(
    use_case_key: str,
    context: dict[str, str],
    output_format_key: str,
) -> PromptDraft: ...
```

MVP logic:

- Use deterministic templates.
- Include goal/question.
- Include context and constraints.
- Include expected output sections.
- Add hints for empty or weak fields.

### 4.5 `components/renderers.py`

Responsibility:

- Convert run data into Markdown.
- Provide small rendering helpers where useful.

Required export:

```python
def build_markdown_export(
    question: str,
    use_case_title: str,
    safety_level: str,
    board_title: str,
    output_format_title: str,
    synthesis: str,
    director_messages: list[dict],
) -> str: ...
```

Required Markdown sections:

- `# Board of Directors Ergebnis`
- `## Fragestellung`
- `## Use Case`
- `## Safety Einstufung`
- `## Board`
- `## Output Format`
- `## Synthese`
- `## Director-Beitraege`

### 4.6 `components/api_client.py`

Responsibility:

- Provide a backend API client.
- Provide a mock client with the same UI-facing interface.
- Normalize API errors into German user-facing messages.

Suggested classes:

```python
class BoardApiError(Exception):
    pass

class BoardApiClient:
    def list_directors(self) -> list[dict]: ...
    def list_boards(self) -> list[dict]: ...
    def start_run(self, board_id: str, question: str, **overrides) -> dict: ...
    def get_run(self, run_id: str) -> dict: ...
    def stream_messages(self, run_id: str): ...
    def cancel_run(self, run_id: str) -> None: ...

class MockBoardApiClient:
    def list_directors(self) -> list[dict]: ...
    def list_boards(self) -> list[dict]: ...
    def start_run(self, board_id: str, question: str, **overrides) -> dict: ...
    def get_run(self, run_id: str) -> dict: ...
    def stream_messages(self, run_id: str): ...
    def cancel_run(self, run_id: str) -> None: ...
```

### 4.7 `components/auth.py`

Responsibility:

- Encapsulate access token retrieval.
- Keep MVP simple.

MVP options:

1. Read token from `st.session_state["entra_access_token"]` if present.
2. Return `None` in local mock mode.
3. Do not implement complex Entra login unless existing app already provides it.

### 4.8 `components/state.py`

Responsibility:

- Initialize and manage Streamlit session-state keys.

Suggested keys:

```python
DEFAULT_STATE = {
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
    "mock_mode": False,
}
```

Required exports:

```python
def init_session_state() -> None: ...
def reset_wizard() -> None: ...
```

---

## 5. Page design

### 5.1 `pages/01_Start.py`

Responsibilities:

- Show value proposition.
- Show safety hints.
- Show use-case entry buttons.
- Show recent runs if backend is available, otherwise mock/demo content.

### 5.2 `pages/02_Neues_Sparring.py`

Responsibilities:

- Implement wizard.
- Render one step at a time.
- Use session state.
- Call safety, prompt coach, API/mock client and renderers.

### 5.3 `pages/03_Meine_Runs.py`

Responsibilities:

- Show previous runs if backend supports it.
- MVP may show placeholder plus current session runs.

### 5.4 `pages/04_Board_Bibliothek.py`

Responsibilities:

- Show static board templates.
- Explain when to use each board.
- No advanced board editing required for MVP.

### 5.5 `pages/05_Hilfe_Leitplanken.py`

Responsibilities:

- Explain safe usage.
- Give examples of allowed and disallowed input.
- Explain yellow and red classifications.

---

## 6. Run data model used by UI

Normalize backend and mock runs into this UI shape:

```python
{
    "id": "run_mock_001",
    "status": "pending|running|done|failed|cancelled",
    "question": "...",
    "synthesis": "...",
    "messages": [
        {
            "role": "Stratege",
            "round": 1,
            "content": "..."
        }
    ],
    "error": None,
}
```

The UI should tolerate missing optional fields.

---

## 7. Deployment design

Streamlit container:

- Base image: `python:3.11-slim`.
- Exposes port `8501`.
- Starts with `streamlit run streamlit_app/app.py --server.port=8501 --server.address=0.0.0.0`.

Target Azure resources:

- Container App `streamlit`.
- Existing Container App `api`.
- Existing Container App `worker`.
- Existing Azure Container Registry.
- Existing Application Insights / Log Analytics.

Streamlit app environment variables:

- `BOARD_API_BASE_URL`
- `APP_ENV`
- `AUTH_DEV_BYPASS`
- optionally `AZURE_TENANT_ID`
- optionally `AZURE_CLIENT_ID`
- optionally `AZURE_API_SCOPE`

---

## 8. Design decisions

### DD-001 Safety local first

MVP safety is implemented locally in Streamlit to reduce backend scope and allow immediate UX validation.

### DD-002 Prompt coach local first

MVP prompt coach is deterministic and local to avoid extra LLM cost and reduce compliance surface.

### DD-003 Mock mode first

UI must work without backend so the WebUI can be tested independently.

### DD-004 Generic Streamlit only

No custom frontend stack. UX must use native Streamlit patterns rather than pixel-perfect custom UI.
