# ADR-0003: Mock Mode Required

## Status

Accepted

## Context

The Streamlit WebUI should be developed and tested independently from backend availability, Azure availability and LLM provider availability.

## Decision

The WebUI must support a mock mode when `BOARD_API_BASE_URL` is not configured.

## Consequences

- Coding agents and developers can validate the full user journey locally.
- UI development is decoupled from backend infrastructure.
- Mock client must mimic the UI-facing shape of the real API client.
- Mock mode must be visibly indicated to users.

## Validation

- App starts without backend configuration.
- Full guided flow completes in mock mode.
- Markdown export works in mock mode.
