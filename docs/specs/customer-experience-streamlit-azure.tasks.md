# Tasks: Customer-Experience Streamlit Azure

Status: Draft  
Parent spec: `docs/specs/customer-experience-streamlit-azure.md`  
Requirements: `docs/specs/customer-experience-streamlit-azure.requirements.md`  
Design: `docs/specs/customer-experience-streamlit-azure.design.md`

---

## 1. Execution rules for coding agents

1. Work task by task in order.
2. Do not skip validation for completed tasks.
3. Keep changes small and reviewable.
4. Do not implement optional backend endpoints before the MVP Streamlit flow works.
5. Keep UI copy German.
6. Keep Streamlit generic.
7. Use mock mode as the first end-to-end target.
8. Do not commit secrets or local configuration files with credentials.

---

## 2. Milestones

| Milestone | Goal | Backend required |
|---|---|---:|
| M1 | Streamlit skeleton starts | No |
| M2 | Templates and safety tested | No |
| M3 | Guided flow works in mock mode | No |
| M4 | Markdown export works | No |
| M5 | Existing backend runs integrate | Yes |
| M6 | Azure container is buildable | No |
| M7 | Azure deployment files updated | Partly |

---

## 3. Task list

## Task 1: Create Streamlit skeleton

### Objective

Create the minimal Streamlit app structure without backend dependency.

### Files to create

- `streamlit_app/app.py`
- `streamlit_app/requirements.txt`
- `streamlit_app/components/__init__.py`
- `streamlit_app/components/state.py`
- `streamlit_app/pages/01_Start.py`

### Implementation notes

- Use `st.set_page_config`.
- Initialize session state in `components/state.py`.
- Start page should show title, value proposition, safety hints and placeholder use-case buttons.
- Do not add backend calls yet.

### Acceptance criteria

- App starts with `streamlit run streamlit_app/app.py`.
- No backend configuration is required.
- Sidebar or navigation exists.
- UI is German.

### Validation

```bash
python -m compileall streamlit_app
```

---

## Task 2: Implement template registry

### Objective

Add use-case, board and output-format templates as pure Python registry.

### Files to create or change

- `streamlit_app/components/templates.py`
- `streamlit_app/tests/test_templates.py`

### Required use cases

- `decision_brief`
- `communication_review`
- `project_structuring`
- `risk_challenge`
- `strategy_sparring`
- `concept_challenge`

### Required board templates

- `management_board`
- `banking_governance_board`
- `communication_board`
- `project_delivery_board`
- `learning_board`

### Required output formats

- `executive_summary`
- `decision_brief`
- `project_brief`
- `communication_draft`
- `risk_log`
- `todo_plan`
- `one_pager`

### Acceptance criteria

- Each use case has a valid recommended board.
- Each use case has a valid recommended output format.
- `validate_template_references()` returns an empty list.
- Tests cover required registries and references.

### Validation

```bash
python -m pytest streamlit_app/tests/test_templates.py
```

---

## Task 3: Implement deterministic safety assessment

### Objective

Add rule-based safety classification with green, yellow and red levels.

### Files to create or change

- `streamlit_app/components/safety.py`
- `streamlit_app/tests/test_safety.py`

### Required behavior

- IBAN-like input is red.
- Email-like input is red.
- Kundennummer / Kontonummer keywords are red.
- Internal strategy or budget terms are yellow.
- Harmless generic question is green.

### Acceptance criteria

- `assess_safety()` returns a `SafetyAssessment` object.
- Red means `can_continue == False`.
- Yellow means `can_continue == True` but UI must later require confirmation.
- Green means `can_continue == True`.
- Tests cover all three levels.

### Validation

```bash
python -m pytest streamlit_app/tests/test_safety.py
```

---

## Task 4: Implement prompt coach

### Objective

Generate an editable prompt draft from structured context.

### Files to create or change

- `streamlit_app/components/prompt_coach.py`
- `streamlit_app/tests/test_prompt_coach.py`

### Required behavior

- Use deterministic local templates.
- Include selected use case.
- Include user goal/question.
- Include context fields.
- Include output format instruction.
- Generate quality hints for missing or weak fields.

### Acceptance criteria

- Prompt draft includes core user input.
- Missing context produces at least one quality hint.
- No backend or LLM call is used.

### Validation

```bash
python -m pytest streamlit_app/tests/test_prompt_coach.py
```

---

## Task 5: Implement Markdown renderer and export helper

### Objective

Create reusable Markdown export generation.

### Files to create or change

- `streamlit_app/components/renderers.py`
- `streamlit_app/tests/test_renderers.py`

### Required behavior

Markdown export includes:

- title,
- question,
- use case,
- safety level,
- board,
- output format,
- synthesis,
- director messages.

### Acceptance criteria

- Markdown export is deterministic.
- Empty director messages do not break export.
- Tests verify required sections.

### Validation

```bash
python -m pytest streamlit_app/tests/test_renderers.py
```

---

## Task 6: Implement mock API client

### Objective

Allow full UI flow without backend configuration.

### Files to create or change

- `streamlit_app/components/api_client.py`
- optionally `streamlit_app/tests/test_api_client.py`

### Required behavior

- `MockBoardApiClient` implements the same UI-facing interface as `BoardApiClient`.
- Mock run returns a run id, status and sample messages.
- Mock streaming yields deterministic director messages.
- Mock mode is visibly indicated in the UI.

### Acceptance criteria

- Full guided flow can complete without `BOARD_API_BASE_URL`.
- UI shows that mock mode is active.

### Validation

```bash
python -m compileall streamlit_app
```

---

## Task 7: Implement guided sparring page

### Objective

Build the Streamlit wizard for the complete guided flow in mock mode.

### Files to create or change

- `streamlit_app/pages/02_Neues_Sparring.py`
- `streamlit_app/components/state.py`
- `streamlit_app/pages/01_Start.py`

### Required wizard steps

1. Use case selection.
2. Context entry.
3. Safety assessment.
4. Prompt coach review.
5. Board and output format confirmation.
6. Run execution and result display.

### Required behavior

- Red safety blocks run start.
- Yellow safety requires checkbox confirmation.
- User can edit prompt draft.
- Default board and output format come from selected use case.
- Markdown export button is available after result.

### Acceptance criteria

- A user can complete the flow in mock mode.
- Session state preserves values across steps.
- User can reset the wizard.

### Validation

```bash
python -m compileall streamlit_app
python -m pytest streamlit_app/tests
```

---

## Task 8: Implement board library and help pages

### Objective

Expose templates and safety guidance for non-technical users.

### Files to create or change

- `streamlit_app/pages/04_Board_Bibliothek.py`
- `streamlit_app/pages/05_Hilfe_Leitplanken.py`

### Acceptance criteria

- Board library lists all board templates and use cases.
- Help page explains green, yellow and red safety levels.
- Help page includes safe and unsafe example patterns using synthetic data only.

### Validation

```bash
python -m compileall streamlit_app
```

---

## Task 9: Implement real backend API client

### Objective

Connect the Streamlit app to the existing FastAPI backend when `BOARD_API_BASE_URL` is configured.

### Files to create or change

- `streamlit_app/components/api_client.py`
- `streamlit_app/components/auth.py`
- `streamlit_app/pages/02_Neues_Sparring.py`

### Required behavior

- Use `BOARD_API_BASE_URL` from environment.
- Use bearer token from session state if available.
- Support `start_run`, `get_run`, `stream_messages`, `cancel_run` where backend supports them.
- Normalize HTTP errors into German user-facing messages.

### Acceptance criteria

- Mock mode still works.
- Backend mode is selected when base URL is configured.
- Error mapping works for 401, 403, 404, 422, 429 and 5xx.

### Validation

```bash
python -m compileall streamlit_app
python -m pytest streamlit_app/tests
```

---

## Task 10: Implement run history page

### Objective

Show current session runs and, if backend supports it, persisted runs.

### Files to create or change

- `streamlit_app/pages/03_Meine_Runs.py`
- `streamlit_app/components/api_client.py`
- `streamlit_app/components/state.py`

### MVP behavior

- Show current session run history in mock mode.
- In backend mode, show available run list if existing backend endpoint supports it.
- If no backend list endpoint exists, show clear placeholder and current run only.

### Acceptance criteria

- Page does not crash without backend.
- Page explains limitations if persisted run list is unavailable.

### Validation

```bash
python -m compileall streamlit_app
```

---

## Task 11: Add Streamlit Docker packaging

### Objective

Make the Streamlit app container-buildable.

### Files to create or change

- `streamlit_app/Dockerfile`
- `streamlit_app/.streamlit/config.toml`
- optionally `.dockerignore`

### Required behavior

- Container exposes port `8501`.
- Container starts Streamlit on `0.0.0.0`.
- No secrets are copied.

### Acceptance criteria

- Docker build succeeds.

### Validation

```bash
docker build -f streamlit_app/Dockerfile .
```

---

## Task 12: Add Streamlit CI workflow

### Objective

Add basic CI validation for the Streamlit app.

### Files to create or change

- `.github/workflows/streamlit-ci.yml`

### Required checks

- Install Streamlit requirements.
- Compile Python files.
- Run Streamlit tests.
- Run ruff if project already uses ruff or add a minimal compatible invocation.

### Acceptance criteria

- CI can run without backend secrets.
- CI does not require Azure access.

---

## Task 13: Extend Azure IaC for Streamlit Container App

### Objective

Add deployment resources or documented placeholders for a Streamlit Azure Container App.

### Files to inspect first

- `infra/main.bicep`
- existing deployment docs
- existing GitHub Actions workflows

### Files to create or change

- `infra/main.bicep` or additional Bicep module
- `docs/streamlit-azure-deployment.md`

### Required behavior

- Define Container App `streamlit`.
- Configure port `8501`.
- Inject `BOARD_API_BASE_URL` and environment variables.
- Use ACR image reference.
- Do not add secrets in plaintext.

### Acceptance criteria

- IaC remains syntactically valid.
- Deployment docs explain required variables.

---

## Task 14: Final documentation update

### Objective

Document how to run, test and deploy the Streamlit UI.

### Files to create or change

- `README.md` or `docs/streamlit-azure-deployment.md`

### Required content

- Local mock mode.
- Local backend mode.
- Required environment variables.
- Docker build command.
- Azure deployment notes.
- Known limitations.

---

## 4. Recommended PR slicing

### PR 1: Agentic specs only

- `AGENTS.md`
- requirements/design/tasks/validation spec files

### PR 2: Streamlit MVP in mock mode

Tasks 1 to 8.

### PR 3: Backend integration

Tasks 9 and 10.

### PR 4: Container and CI

Tasks 11 and 12.

### PR 5: Azure deployment

Tasks 13 and 14.

---

## 5. Stop conditions

Stop and report instead of guessing if:

1. Existing backend endpoint contracts differ materially from the spec.
2. The repo already contains a conflicting Streamlit app structure.
3. Azure IaC uses a different deployment pattern than assumed.
4. Authentication is already implemented in another app and needs reuse.
5. Required secrets or tenant IDs are unavailable.

In those cases, implement what is safe and leave explicit TODOs.
