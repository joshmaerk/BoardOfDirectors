# ADR-0005: No Runtime Dependency on Agentic Tooling

## Status

Accepted

## Context

The repository references agentic coding tools to improve implementation workflow, command-output handling and coding-agent communication. These tools support development, not product runtime behavior.

## Decision

Agentic coding tools are documented as development-time helpers only. They are not product runtime dependencies and are not required for CI to pass.

## Consequences

- The application remains independent from coding-agent tooling.
- CI and deployment do not depend on local agent tools.
- Coding agents should state whether the tools were available or used.
- Missing agent tools must not block implementation.

## Validation

- Runtime dependency files do not require agentic coding tools.
- CI workflows do not require agentic coding tools.
- Agent instructions reference the toolchain as optional development support.
