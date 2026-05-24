# Contributing

This repository supports agentic coding workflows. Human and AI contributors must follow the same quality and security expectations.

## Read first

- `AGENTS.md`
- `CLAUDE.md` if Claude or Claude Code is used
- `docs/specs/agentic-coding-toolchain.md`
- Relevant task and validation specs under `docs/specs/`

## Development principles

- Make small, focused changes.
- Avoid unrelated refactoring.
- Add tests for new pure logic.
- Keep Streamlit generic.
- Keep user-facing UI text German unless a technical identifier requires English.
- Do not commit real customer, employee, account or production data.

## Local validation

For Streamlit work:

```bash
python -m compileall streamlit_app
python -m pytest streamlit_app/tests
ruff check streamlit_app
```

Or use:

```bash
make validate-streamlit
```

For Docker-related Streamlit changes:

```bash
make docker-streamlit
```

## Pull requests

Every PR should explain:

1. What changed.
2. Why it changed.
3. Which validations were run.
4. Known limitations.
5. Whether the agentic coding toolchain was available or used.

## Agent tasks

Use the `Agent Task` issue template for coding-agent-ready tasks. Include scope, non-scope, acceptance criteria and validation commands.
