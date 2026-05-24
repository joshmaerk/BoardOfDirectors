---
applyTo: "infra/**/*.bicep,infra/**/*.json,.github/workflows/**/*.yml,.github/workflows/**/*.yaml,docs/**/*deployment*.md"
---

# Azure and Deployment Instructions

- Target Azure Container Apps.
- Do not commit plaintext secrets.
- Use environment variables, Container App secrets, Key Vault references or managed identity for sensitive configuration.
- Keep Streamlit on port `8501`.
- Ensure deployment changes are documented.
- If CI/CD is changed, keep workflows runnable without production secrets unless deployment is explicitly required.
- Prefer additive IaC changes over large rewrites.
