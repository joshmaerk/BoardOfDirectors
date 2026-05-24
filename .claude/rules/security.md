# Security Rule

- Do not commit secrets, tokens, private keys, passwords or local `.env` files.
- Do not use real customer or employee data in tests, fixtures, docs or examples.
- Do not log full prompts by default.
- Treat prompt persistence as security-relevant and document it.
- Red safety assessment must block run start by default.
- Yellow safety assessment must require explicit confirmation.
- If a task touches auth, roles, ownership, data export or deletion, call it out in the final response.
