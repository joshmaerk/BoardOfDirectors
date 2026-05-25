## What changed?

-

## Why?

-

## Scope control

- [ ] Only requested files were changed
- [ ] No unrelated refactoring
- [ ] No unrelated formatting changes
- [ ] No secrets or real customer data committed
- [ ] User-facing UI copy is German where applicable

## Validation

Check all that apply:

- [ ] `python -m compileall streamlit_app`
- [ ] `python -m pytest streamlit_app/tests`
- [ ] `ruff check streamlit_app`
- [ ] `docker build -f streamlit_app/Dockerfile .` if Docker files changed
- [ ] Backend validation commands if backend code changed
- [ ] Not run; reason documented below
- [ ] `CHANGELOG.md` wurde mit PR-Nummer, Datum und nutzerlesbaren Einträgen aktualisiert

## Agentic setup

- [ ] `AGENTS.md` followed
- [ ] `CLAUDE.md` followed if Claude was used
- [ ] `docs/specs/agentic-coding-toolchain.md` considered
- [ ] Availability/use of rtk/caveman documented in final notes

## Security and data handling

- [ ] No full prompts logged by default
- [ ] No real customer, employee, account or production data used in tests
- [ ] Safety behavior preserved: red blocks, yellow requires confirmation

## Known limitations / TODOs

-
