# Security Policy

## Scope

This project handles AI prompts, run metadata and potentially internal business context. Treat security and data handling as product requirements.

## Reporting

Report security concerns through the repository owner or the organization's approved security channel. Do not open public issues containing sensitive details.

## Data handling rules

- Do not commit secrets, credentials or local environment files.
- Do not include real customer, employee, account, contract or production data in tests, fixtures or examples.
- Do not log full user prompts by default.
- Treat prompt persistence, exports, audit logs and account deletion as security-relevant.
- Red safety classification must block run start by default.
- Yellow safety classification must require explicit confirmation.

## Development expectations

- Use synthetic data only.
- Keep auth and ownership checks intact.
- Prefer least-privilege configuration in Azure.
- Document security-relevant behavior changes in PRs.
