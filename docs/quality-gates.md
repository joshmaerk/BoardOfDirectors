# Quality Gates

This document defines the minimum quality gates for human and agentic coding work.

## General gates

- Changes are small and scoped.
- No unrelated refactoring.
- No unrelated formatting-only changes.
- No real customer, employee, account or production data in code, tests or docs.
- No local environment files committed.
- User-facing UI copy is German where applicable.

## Streamlit gates

Required for Streamlit changes:

```bash
python -m compileall streamlit_app
python -m pytest streamlit_app/tests
ruff check streamlit_app
```

Additional if Docker files changed:

```bash
docker build -f streamlit_app/Dockerfile .
```

## Backend gates

Required for backend changes:

- Run the existing backend tests from README or CI.
- Run type checks if backend modules are changed.
- Preserve ownership and authorization behavior.
- Document any API contract change.

## Security gates

- Do not log full prompts by default.
- Red safety blocks run start.
- Yellow safety requires explicit confirmation.
- Data-handling behavior is documented if changed.

## Agentic coding gates

Every coding-agent PR must state:

1. Files changed.
2. Validation commands run.
3. Whether the agentic toolchain was available or used.
4. Known limitations.
5. Remaining TODOs.
