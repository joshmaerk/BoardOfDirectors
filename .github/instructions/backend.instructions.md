---
applyTo: "app/**/*.py,conductor/**/*.py"
---

# Backend Instructions

- Keep FastAPI as the backend architecture.
- Read `README.md` and `docs/architecture.md` before changing backend behavior.
- Do not change public API contracts unless the task explicitly requires it.
- Add or update tests for changed backend behavior.
- Preserve ownership and authorization checks.
- Do not log full prompts, access tokens, API keys or personal data.
- Prefer small route/service changes over broad refactoring.
- If database models or migrations are changed, document the migration impact.
