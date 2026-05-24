# Runbook: Azure Deployment

## Purpose

This runbook documents deployment expectations for the Streamlit WebUI and related services.

## Target runtime

The project targets an Azure-oriented container runtime. API, worker and Streamlit should be deployable as separate containerized services.

## Streamlit requirements

- Container listens on port `8501`.
- Runtime configuration is provided through environment variables.
- `BOARD_API_BASE_URL` points to the backend API base URL.
- No environment-specific sensitive values are committed.

## Required environment variables

- `APP_ENV`
- `BOARD_API_BASE_URL`
- `AUTH_DEV_BYPASS`
- optional `AZURE_TENANT_ID`
- optional `AZURE_CLIENT_ID`
- optional `AZURE_API_SCOPE`

## Validation before deployment

```bash
python -m compileall streamlit_app
python -m pytest streamlit_app/tests
ruff check streamlit_app
docker build -f streamlit_app/Dockerfile .
```

## Deployment checks

After deployment:

1. Open the WebUI endpoint.
2. Confirm the app loads.
3. Confirm mock mode is not shown if backend URL is configured.
4. Complete a green safety run.
5. Confirm logs do not contain full prompts or sensitive values.

## Notes

Infrastructure changes should be reviewed through pull requests and aligned with ADR-0004.
