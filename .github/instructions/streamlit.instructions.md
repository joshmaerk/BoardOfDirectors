---
applyTo: "streamlit_app/**/*.py"
---

# Streamlit Instructions

- Use generic Streamlit only.
- Keep UI text German unless a technical identifier requires English.
- Keep page files thin. Put reusable logic into `streamlit_app/components/`.
- Do not add custom frontend frameworks or JavaScript build tooling.
- Keep mock mode working without backend configuration.
- Do not log full user prompts by default.
- Add unit tests for new pure functions in `streamlit_app/tests/`.
- Prefer deterministic local logic for MVP safety and prompt coach.
- Red safety blocks run start.
- Yellow safety requires explicit confirmation.
