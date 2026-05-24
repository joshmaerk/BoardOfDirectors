# CLAUDE.md

Behavioral guidelines for Claude and Claude Code when working in this repository.

These guidelines reduce common LLM coding mistakes. They are intentionally biased toward caution over speed. For trivial tasks, use judgment.

Project-specific instructions are in `AGENTS.md`. When instructions conflict, follow the stricter instruction and preserve the repository constraints.

---

## 1. Think before coding

**Do not assume. Do not hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly.
- If uncertain, ask before coding.
- If multiple interpretations exist, present them instead of silently choosing one.
- If a simpler approach exists, say so.
- Push back when the requested solution is likely overbuilt or risky.
- If something is unclear, stop, name what is confusing, and ask.

For multi-step work, provide a brief plan before editing:

```text
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

---

## 2. Simplicity first

**Minimum code that solves the problem. Nothing speculative.**

Rules:

- Do not add features beyond what was requested.
- Do not add abstractions for single-use code.
- Do not add configurability that was not requested.
- Do not add error handling for impossible or irrelevant scenarios.
- If 200 lines could be 50, rewrite it.
- Prefer readable plain Python over clever patterns.
- Prefer deterministic local logic for MVP behavior unless the spec requires a service call.

Ask before finalizing:

> Would a senior engineer say this is overcomplicated?

If yes, simplify.

---

## 3. Surgical changes

**Touch only what is necessary. Clean up only your own mess.**

When editing existing code:

- Do not improve adjacent code, comments, or formatting unless required.
- Do not refactor things that are not broken.
- Match existing style, even if you would normally do it differently.
- If unrelated dead code is noticed, mention it in the final response instead of deleting it.

When your changes create orphans:

- Remove imports, variables, functions and files that your changes made unused.
- Do not remove pre-existing dead code unless explicitly asked.

Test:

> Every changed line should trace directly to the user's request.

---

## 4. Goal-driven execution

**Define success criteria. Loop until verified.**

Transform broad tasks into verifiable goals:

- `Add validation` -> write tests for invalid inputs, then make them pass.
- `Fix the bug` -> write a test that reproduces it, then make it pass.
- `Refactor X` -> ensure tests pass before and after.
- `Build feature Y` -> implement the smallest path through the user journey, then validate it.

For this repository, prefer the task and validation files:

- `docs/specs/customer-experience-streamlit-azure.tasks.md`
- `docs/specs/customer-experience-streamlit-azure.validation.md`

Do not claim completion without running the relevant validation commands or explicitly saying why they could not be run.

---

## 5. Repository-specific behavior

Follow `AGENTS.md` for repository-wide constraints. Especially:

- Use generic Streamlit only for the WebUI.
- Do not introduce React, Next.js, Vue, Angular, Svelte or custom frontend build systems.
- Keep FastAPI as backend.
- Target Azure Container Apps deployment.
- Do not commit secrets.
- UI copy must be German unless technical identifiers require English.
- Keep MVP safety and prompt coach local in Streamlit unless explicitly instructed otherwise.
- Do not implement optional backend endpoints before the MVP Streamlit flow works.

---

## 6. These guidelines are working if

- Diffs are smaller and easier to review.
- There are fewer unnecessary rewrites.
- Clarifying questions come before implementation mistakes.
- Tests or smoke checks are tied to each implementation step.
- The final response clearly states what changed, what was verified and what remains open.
