---
applyTo: "**/tests/**/*.py,tests/**/*.py,streamlit_app/tests/**/*.py"
---

# Testing Instructions

- Use synthetic data only.
- Do not include real customer, employee, account, contract or production data.
- Prefer small deterministic tests.
- Test pure functions directly.
- For safety classification, cover green, yellow and red cases.
- For renderers, assert required sections rather than exact full text where possible.
- Keep tests independent of Azure, external LLM providers and live backend services unless explicitly marked as integration tests.
