# Agentic Coding Toolchain

This repository uses the following agentic coding tooling references:

- `rtk-ai/rtk`: token-efficient command-output layer for coding agents.
- `JuliusBrussee/caveman`: brevity and output-compression layer for Claude Code and other coding agents.

## Usage policy

- Prefer `rtk` for compact command output when it is available.
- Prefer `caveman` for concise coding-agent communication when it is available.
- Missing tools are not blockers.
- Continue with standard commands when these tools are unavailable.
- State in the final response whether these tools were available or used.

## Boundaries

- Do not add product runtime dependencies on these tools.
- Do not require these tools for CI.
- Do not rewrite repository instruction files into compressed style unless explicitly requested.
- Do not perform tool installation unless the execution environment explicitly permits it.
