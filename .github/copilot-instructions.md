# Copilot Instructions

Read these files first:

1. `AGENTS.md`
2. `CLAUDE.md` if Claude-style instructions are relevant
3. `docs/specs/customer-experience-streamlit-azure.tasks.md`
4. `docs/specs/customer-experience-streamlit-azure.validation.md`
5. `docs/specs/agentic-coding-toolchain.md`

## Core constraints

- Use generic Streamlit only for the WebUI.
- Do not introduce React, Next.js, Vue, Angular, Svelte or custom frontend build systems.
- Keep FastAPI as backend.
- Target Azure Container Apps deployment.
- UI copy must be German unless technical identifiers require English.
- Do not commit secrets or real customer data.
- Keep MVP safety and prompt coach local in Streamlit unless explicitly instructed otherwise.
- Do not implement optional backend endpoints before the MVP Streamlit flow works.

## Working style

- Make small, surgical changes.
- Avoid unrelated refactoring.
- Add tests for new pure functions.
- Prefer mock-mode implementation before backend coupling.
- Run relevant validation commands before claiming completion.
