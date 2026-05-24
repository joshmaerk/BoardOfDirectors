# Backend Rule

Applies to FastAPI, worker, conductor and backend-related code.

- Read `README.md` and `docs/architecture.md` before changing backend behavior.
- Keep FastAPI as the backend architecture.
- Do not change public API contracts unless explicitly required.
- Preserve ownership and authorization checks.
- Do not log full prompts, access tokens, API keys or personal data.
- Add or update tests for changed backend behavior.
- Prefer small route/service changes over broad refactoring.
- If database models or migrations are changed, document the migration impact.
