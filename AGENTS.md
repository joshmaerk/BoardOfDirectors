# AGENTS.md

## Project context

`BoardOfDirectors` is a Python/FastAPI/Streamlit application for AI-powered board-style sparring. The product goal is to help internal expert users, project leads and managers use AI safely and productively, even if their current AI maturity is low.

The relevant product specification is:

- `docs/specs/customer-experience-streamlit-azure.md`

The implementation must follow the companion files:

- `docs/specs/customer-experience-streamlit-azure.requirements.md`
- `docs/specs/customer-experience-streamlit-azure.design.md`
- `docs/specs/customer-experience-streamlit-azure.tasks.md`
- `docs/specs/customer-experience-streamlit-azure.validation.md`

---

## Non-negotiable constraints

1. Use generic Streamlit only for the WebUI.
2. Do not introduce React, Next.js, Vue, Angular, Svelte, custom JavaScript build systems, or proprietary UI frameworks.
3. Keep FastAPI as the backend architecture.
4. Target Azure Container Apps deployment.
5. Do not commit secrets, credentials, API keys, access tokens, tenant secrets, private keys or local `.env` files.
6. Do not log full user prompts by default.
7. UI copy must be German unless technical API names require English.
8. Prefer small, reviewable commits.
9. Keep MVP safety and prompt coach local in Streamlit unless explicitly instructed otherwise.
10. Do not implement optional backend endpoints before the MVP WebUI works in mock mode and against existing backend endpoints.

---

## Implementation order

Implement in this order unless the user explicitly asks otherwise:

1. Streamlit skeleton.
2. Static templates.
3. Rule-based safety assessment.
4. Rule-based prompt coach.
5. Markdown rendering and export.
6. Mock run mode.
7. Existing backend API integration.
8. SSE streaming integration.
9. Azure Container App packaging.
10. Optional backend persistence extensions.

---

## Repository working rules

- Read the existing README and architecture docs before changing backend code.
- Do not change public backend API contracts unless the change is necessary and documented.
- Do not rename existing app packages unless required.
- Keep new Streamlit code under `streamlit_app/` unless the repository already contains a Streamlit app that should be extended.
- Keep pure functions in modules under `streamlit_app/components/` and test them.
- Keep UI pages thin; page files should orchestrate state and rendering, not contain complex business logic.
- Use type hints for new Python modules.
- Avoid hard-coded absolute local paths.
- Make mock mode explicit and visible in the UI.

---

## Streamlit rules

Allowed native Streamlit primitives include:

- `st.set_page_config`
- `st.sidebar`
- `st.tabs`
- `st.expander`
- `st.form`
- `st.columns`
- `st.status`
- `st.progress`
- `st.spinner`
- `st.toast`
- `st.dataframe`
- `st.download_button`
- `st.session_state`

Do not add custom front-end frameworks. Small inline CSS is acceptable only if it is non-essential and does not create a custom design system.

---

## Security and compliance rules

- Never include real customer data in tests, fixtures or examples.
- Use synthetic data only.
- Red safety assessment must block run start by default.
- Yellow safety assessment must require explicit user confirmation.
- Green safety assessment may proceed without confirmation.
- Do not store safety-sensitive raw prompts in logs.
- If prompt persistence is introduced, document where it is stored and how deletion/export works.

---

## Validation commands

Run these before considering the implementation complete:

```bash
python -m compileall streamlit_app
python -m pytest streamlit_app/tests
ruff check streamlit_app
```

If Docker files are touched, also run:

```bash
docker build -f streamlit_app/Dockerfile .
```

If backend code is touched, also run the repository's existing backend validation commands from the README or CI configuration.

---

## Expected final response from coding agents

When done, summarize:

1. Files created or changed.
2. Features implemented.
3. Validation commands run and their results.
4. Known limitations.
5. Remaining TODOs.
