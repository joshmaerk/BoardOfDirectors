# ADR-0004: Cloud Container Runtime

## Status

Accepted

## Context

The product has separate Python services for API, worker and WebUI. The runtime should support independently deployable containers.

## Decision

Use the existing Azure-oriented container runtime approach for API, worker and Streamlit.

## Consequences

- Services can be packaged independently.
- Streamlit listens on port `8501`.
- Runtime configuration is environment-specific.
- Deployment documentation must stay aligned with infrastructure files.

## Validation

- WebUI image builds.
- Required environment variables are documented.
- Infrastructure changes are reviewed through pull requests.
