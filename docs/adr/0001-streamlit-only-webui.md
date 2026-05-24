# ADR-0001: Streamlit-only WebUI

## Status

Accepted

## Context

The WebUI is intended for internal expert users with low AI maturity. The implementation should stay simple, reviewable and deployable in Azure without a separate frontend build chain.

## Decision

The WebUI will be implemented with generic Streamlit only.

No React, Next.js, Vue, Angular, Svelte, custom JavaScript build systems or proprietary UI frameworks will be introduced.

## Consequences

- Faster implementation and simpler operations.
- Lower frontend complexity.
- Less pixel-perfect control than a custom SPA.
- UI patterns must use native Streamlit primitives.

## Validation

Pull requests touching WebUI must verify that no custom frontend stack was added.
