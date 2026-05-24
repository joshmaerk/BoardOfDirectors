# ADR-0002: Local Safety First for MVP

## Status

Accepted

## Context

The guided Streamlit MVP needs immediate safety feedback before a run starts. A full backend governance service would increase scope and delay UX validation.

## Decision

For MVP, safety assessment is deterministic and local in the Streamlit app.

## Consequences

- The guided flow can work in mock mode without backend dependency.
- Safety feedback is fast and testable.
- The local classifier is not a complete DLP solution.
- Backend persistence and centralized governance can be added later.

## Validation

- Red examples block run start.
- Yellow examples require explicit confirmation.
- Green examples proceed without additional confirmation.
