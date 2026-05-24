# Runbook: Local Development

## Purpose

This runbook describes the local workflow for humans and coding agents.

## Read first

- `AGENTS.md`
- `CLAUDE.md`
- `docs/specs/customer-experience-streamlit-azure.tasks.md`
- `docs/specs/customer-experience-streamlit-azure.validation.md`

## Environment

1. Use Python 3.11 or newer.
2. Create a local virtual environment.
3. Install backend requirements if needed.
4. Install Streamlit requirements when `streamlit_app/` exists.
5. Copy `.env.example` to `.env` locally if needed. Do not commit `.env`.

## Streamlit mock mode

If `BOARD_API_BASE_URL` is empty, the Streamlit app should run in mock mode.

Expected behavior:

- App starts without backend.
- Mock mode is visible.
- Guided flow can be completed.
- Markdown export works.

## Validation

```bash
make validate-streamlit
```

If Make is unavailable, run:

```bash
python -m compileall streamlit_app
python -m pytest streamlit_app/tests
ruff check streamlit_app
```

## Troubleshooting

- Missing `streamlit_app/`: implement the Streamlit skeleton task first.
- Missing tests: complete the relevant task before claiming validation success.
- Backend unavailable: use mock mode.
