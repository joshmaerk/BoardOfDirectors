# Streamlit Rule

Applies to Streamlit WebUI work.

- Use generic Streamlit only.
- Keep UI copy German unless a technical identifier requires English.
- Keep pages thin and move reusable logic into `streamlit_app/components/`.
- Do not introduce custom frontend frameworks or JavaScript build tooling.
- Keep mock mode working without backend configuration.
- Do not log full user prompts by default.
- Test pure functions in `streamlit_app/tests/`.
- MVP safety and prompt coach remain deterministic and local.
- Red safety blocks run start.
- Yellow safety requires explicit confirmation.
