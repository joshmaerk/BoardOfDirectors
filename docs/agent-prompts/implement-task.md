# Agent Prompt: Implement Task

Use this prompt when asking a coding agent to implement a specific task.

```text
Read first:
1. AGENTS.md
2. CLAUDE.md if using Claude
3. docs/specs/agentic-coding-toolchain.md
4. docs/specs/customer-experience-streamlit-azure.tasks.md
5. docs/specs/customer-experience-streamlit-azure.validation.md

Implement only the requested task: [TASK ID / TASK NAME].

Scope:
- Allowed files: [LIST]
- Disallowed files: [LIST]

Acceptance criteria:
- [CRITERION 1]
- [CRITERION 2]

Validation:
- [COMMAND 1]
- [COMMAND 2]

Rules:
- Do not implement later tasks.
- Do not refactor unrelated code.
- Use synthetic data only.
- Keep Streamlit generic.
- State whether rtk/caveman were available or used.

Final response:
- Files changed
- What was implemented
- Validation results
- Known limitations
- Remaining TODOs
```
