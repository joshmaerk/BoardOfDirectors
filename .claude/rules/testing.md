# Testing Rule

- Use synthetic data only.
- Do not include real customer, employee, account, contract or production data.
- Prefer deterministic unit tests for pure functions.
- Safety tests must cover green, yellow and red classifications.
- Renderer tests should verify required sections rather than brittle full-text matches.
- Mock clients should not call live Azure, LLM providers or production backends.
- If validation cannot be run, state exactly why in the final response.
