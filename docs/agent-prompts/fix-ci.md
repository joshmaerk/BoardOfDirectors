# CI Fix Prompt Template

Read AGENTS.md and docs/quality-gates.md.

Goal: fix the failing validation with the smallest possible change.

Rules:

- Reproduce the failing command locally if possible.
- Do not refactor unrelated code.
- Do not weaken tests to make them pass.
- If the failure is caused by missing implementation, complete the smallest missing piece.
- State which command failed and which command passes after the fix.

Return:

1. Root cause.
2. Files changed.
3. Validation result.
4. Remaining risk.
