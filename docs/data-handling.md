# Data Handling Guidance

## Purpose

This document defines safe handling expectations for prompts, run outputs, test data and examples.

## Allowed for examples and tests

- Synthetic business scenarios.
- Synthetic names only when necessary.
- Generic internal process examples.
- Fake identifiers that are clearly not real.

## Not allowed for examples and tests

- Real customer data.
- Real employee personal data.
- Real account or contract data.
- Production prompts that contain confidential context.
- Access tokens, keys or local environment files.

## Safety levels

### Green

General or synthetic business context without sensitive details.

### Yellow

Internal or potentially confidential business context. The user must explicitly confirm before continuing.

### Red

Personal data, customer data, account data, direct identifiers or similar sensitive content. The run must be blocked by default.

## Logging

- Do not log full prompts by default.
- Log run identifiers, status transitions and technical errors only.
- If additional logging is required for debugging, document it and keep it disabled by default.

## Exports

Markdown exports may contain user-provided prompt content. Treat exported files as user-controlled content and do not store them outside the user's chosen location unless explicitly designed and documented.
