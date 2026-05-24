# Runbook: Incident Troubleshooting

## Purpose

This runbook provides first checks for local, CI and runtime problems.

## First questions

1. Is the issue in Streamlit, backend, worker, infrastructure or CI?
2. Is mock mode active?
3. Was a recent agentic PR merged?
4. Were validation commands run?
5. Does the issue involve data handling, auth or prompt persistence?

## Streamlit checks

- Confirm environment variables.
- Confirm `BOARD_API_BASE_URL` behavior.
- Run local validation.
- Reproduce in mock mode if backend is unavailable.

## Backend checks

- Confirm health endpoint.
- Check API logs for status transitions and technical errors.
- Do not paste full sensitive prompts into issues.

## CI checks

- Identify the failing job.
- Re-run the same command locally.
- If failure is due to missing Streamlit skeleton, complete the relevant task first.

## Security-sensitive incidents

If a concern involves secrets, personal data or confidential prompts:

- Do not open a public issue with details.
- Notify the repository owner or approved security channel.
- Preserve evidence without spreading sensitive content.
