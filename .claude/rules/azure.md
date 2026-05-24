# Azure Rule

- Target Azure Container Apps for deployment work.
- Keep Streamlit on port `8501`.
- Do not commit plaintext secrets in IaC, workflow files or docs.
- Use environment variables, Container App secrets, Key Vault references or managed identity for sensitive configuration.
- CI workflows should run without production Azure credentials unless the task explicitly implements deployment.
- Prefer additive IaC changes over large rewrites.
- Document required deployment variables and manual steps.
