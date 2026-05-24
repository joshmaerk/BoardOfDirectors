# Validation Plan: Customer-Experience Streamlit Azure

Status: Draft  
Parent spec: `docs/specs/customer-experience-streamlit-azure.md`  
Tasks: `docs/specs/customer-experience-streamlit-azure.tasks.md`

---

## 1. Validation philosophy

The implementation must be validated in layers:

1. Pure Python module tests.
2. Streamlit app compile check.
3. Mock-mode UX smoke test.
4. Backend-mode integration smoke test.
5. Docker build validation.
6. Azure deployment validation.

The first working milestone is not Azure deployment. The first working milestone is a complete local mock-mode user journey.

---

## 2. Local development checks

Run from repository root.

### 2.1 Compile Streamlit app

```bash
python -m compileall streamlit_app
```

Expected result:

- No syntax errors.

### 2.2 Run Streamlit tests

```bash
python -m pytest streamlit_app/tests
```

Expected result:

- All tests pass.

### 2.3 Lint Streamlit app

```bash
ruff check streamlit_app
```

Expected result:

- No ruff errors.

If ruff is not yet configured for `streamlit_app`, use the repository's existing ruff configuration or add minimal compatible configuration without weakening existing backend checks.

---

## 3. Required unit tests

### 3.1 Template tests

File:

- `streamlit_app/tests/test_templates.py`

Required tests:

1. All required use cases exist.
2. All required board templates exist.
3. All required output formats exist.
4. Each use case references an existing board.
5. Each use case references an existing output format.
6. `validate_template_references()` returns an empty list.

### 3.2 Safety tests

File:

- `streamlit_app/tests/test_safety.py`

Required tests:

1. Generic harmless strategy question is `green`.
2. Internal budget/strategy text is `yellow`.
3. IBAN-like text is `red`.
4. E-mail-like text is `red`.
5. Customer-number keyword is `red`.
6. Red result has `can_continue == False`.
7. Yellow result has `can_continue == True`.
8. Green result has `can_continue == True`.

Use synthetic data only.

### 3.3 Prompt coach tests

File:

- `streamlit_app/tests/test_prompt_coach.py`

Required tests:

1. Prompt includes user goal.
2. Prompt includes context.
3. Prompt includes output format instruction.
4. Missing context creates quality hint.
5. Function does not require backend or LLM.

### 3.4 Renderer tests

File:

- `streamlit_app/tests/test_renderers.py`

Required tests:

1. Markdown export includes required headings.
2. Markdown export includes question.
3. Markdown export includes safety level.
4. Markdown export includes board title.
5. Empty director messages do not crash export.

### 3.5 API client tests

Optional for MVP but recommended:

- `streamlit_app/tests/test_api_client.py`

Recommended tests:

1. Mock client returns deterministic run.
2. Mock stream yields messages.
3. HTTP error mapping creates German user-facing messages.

---

## 4. Manual mock-mode UX smoke test

Precondition:

- `BOARD_API_BASE_URL` is not set.

Command:

```bash
streamlit run streamlit_app/app.py
```

Steps:

1. Open app in browser.
2. Confirm visible mock-mode indication.
3. Select `Entscheidung vorbereiten`.
4. Enter a harmless business question.
5. Continue to safety step.
6. Confirm safety is green.
7. Review generated prompt.
8. Edit prompt.
9. Confirm recommended board and output format.
10. Start mock run.
11. Confirm director messages or mock result appears.
12. Download Markdown export.
13. Open downloaded Markdown and verify required sections.

Expected result:

- User can complete the full journey without backend.
- No stacktrace is shown.
- UI text is German.

---

## 5. Manual safety smoke tests

### 5.1 Green case

Input:

```text
Wie kann ich die Abstimmung in einem Projektteam klarer strukturieren?
```

Expected:

- Safety level: `green`.
- Run can proceed.

### 5.2 Yellow case

Input:

```text
Wir planen eine interne Strategie mit Budgetannahmen fuer naechstes Jahr.
```

Expected:

- Safety level: `yellow`.
- Reasons are visible.
- Confirmation checkbox is required.
- Run cannot start until checkbox is checked.

### 5.3 Red case

Input:

```text
Bitte analysiere den Fall mit der IBAN AT611904300234573201.
```

Expected:

- Safety level: `red`.
- Run start is blocked.
- Anonymization guidance is visible.

### 5.4 Red e-mail case

Input:

```text
Bitte schreibe eine Bewertung ueber max.mustermann@example.com.
```

Expected:

- Safety level: `red`.
- Run start is blocked.

---

## 6. Backend-mode smoke test

Precondition:

- `BOARD_API_BASE_URL` is set to a reachable FastAPI backend base URL.
- Auth token is available if backend requires it.

Command:

```bash
BOARD_API_BASE_URL="http://localhost:8000/api/v1" streamlit run streamlit_app/app.py
```

Steps:

1. Open app.
2. Confirm mock-mode banner is not shown.
3. Complete guided flow with green safety input.
4. Start backend run.
5. Confirm run status appears.
6. Confirm SSE messages appear if stream endpoint is available.
7. Confirm final result or status can be retrieved.
8. Test cancel button if run is still active.

Expected result:

- Existing backend endpoints are used.
- Backend errors are shown as German user-facing messages.
- No raw stacktrace is shown to end user.

---

## 7. Error handling validation

Simulate or mock the following backend responses:

| HTTP status | Expected UI message |
|---|---|
| 401 | Sitzung abgelaufen oder Zugriff nicht gueltig. Bitte neu anmelden. |
| 403 | Kein ausreichender Zugriff fuer diese Funktion. |
| 404 | Die angeforderte Ressource wurde nicht gefunden oder gehoert nicht zu deinem Zugriff. |
| 422 | Eingabe konnte nicht verarbeitet werden. Bitte pruefe die Angaben. |
| 429 | Zu viele Anfragen. Bitte kurz warten und erneut versuchen. |
| 5xx | Der Dienst ist temporaer nicht verfuegbar. Bitte spaeter erneut versuchen. |

Expected:

- UI does not expose stack traces.
- UI remains usable after the error.

---

## 8. Docker validation

Command:

```bash
docker build -f streamlit_app/Dockerfile .
```

Expected result:

- Image builds successfully.
- No secrets are copied.
- App starts on port `8501`.

Optional run:

```bash
docker run --rm -p 8501:8501 bod-streamlit-test
```

Expected:

- App is reachable at `http://localhost:8501`.

---

## 9. CI validation

A Streamlit CI workflow should perform at least:

```bash
python -m compileall streamlit_app
python -m pytest streamlit_app/tests
ruff check streamlit_app
```

Expected:

- CI runs without backend secrets.
- CI runs without Azure credentials.
- CI fails on missing tests or syntax errors.

---

## 10. Azure deployment validation

### 10.1 Configuration checks

Verify Azure Container App `streamlit` has:

- image reference to ACR image,
- port `8501`,
- `BOARD_API_BASE_URL`,
- `APP_ENV`,
- no plaintext secrets in IaC,
- logging connected to Log Analytics / Application Insights if available.

### 10.2 Runtime checks

After deployment:

1. Open Streamlit endpoint.
2. Confirm app loads.
3. Confirm backend mode is active if `BOARD_API_BASE_URL` is set.
4. Complete a green safety run.
5. Confirm logs show app startup and no secrets.

---

## 11. Security validation

Required checks:

1. Search repository diff for accidental secrets.
2. Verify `.env` files are not committed.
3. Verify test examples use synthetic data only.
4. Verify full prompts are not logged by default.
5. Verify red safety blocks run start.
6. Verify yellow safety requires explicit confirmation.

Recommended commands:

```bash
git diff --check
git grep -n "ANTHROPIC_API_KEY\|AZURE_CLIENT_SECRET\|BEGIN PRIVATE KEY\|password=" -- . || true
```

Interpretation:

- The grep command may find documentation references. Actual secrets must not appear.

---

## 12. Definition of done

The implementation is complete when all of the following are true:

1. Local mock-mode flow works end to end.
2. Required unit tests pass.
3. Streamlit app compiles.
4. Red/yellow/green safety behavior is validated.
5. Markdown export works.
6. Backend mode works with existing endpoints or clearly documents missing backend support.
7. Docker image builds.
8. Azure deployment path is documented or implemented.
9. No secrets are committed.
10. Known limitations are documented.
