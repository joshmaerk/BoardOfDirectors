# Requirements: Customer-Experience Streamlit Azure

Status: Draft  
Parent spec: `docs/specs/customer-experience-streamlit-azure.md`  
Audience: Coding agents, reviewers, product owner

---

## 1. Requirement language

Requirements use a lightweight EARS/Given-When-Then style.

Keywords:

- **THE SYSTEM SHALL**: mandatory.
- **THE SYSTEM SHOULD**: recommended for MVP unless explicitly deferred.
- **THE SYSTEM MAY**: optional.
- **MVP**: must be implemented in the first working version.
- **Future**: documented but not mandatory for MVP.

---

## 2. Product-level requirements

### R-PROD-001 Guided AI sparring

WHEN an internal user opens the WebUI  
THE SYSTEM SHALL present the product as a guided AI sparring tool for expert work, not as a generic empty chat interface.

### R-PROD-002 Low AI maturity support

WHEN a user has low prompt expertise  
THE SYSTEM SHALL guide the user through use-case selection, structured context entry, safety assessment, prompt review and board execution.

### R-PROD-003 German business UI

WHEN user-facing UI text is displayed  
THE SYSTEM SHALL use German business language unless the text is a technical identifier, API name, model name or environment variable.

### R-PROD-004 Work product orientation

WHEN a run is completed  
THE SYSTEM SHALL make the result available as a reusable work product, at minimum as Markdown export.

---

## 3. Streamlit WebUI requirements

### R-UI-001 Generic Streamlit only

THE SYSTEM SHALL implement the WebUI using generic Streamlit primitives only.

THE SYSTEM SHALL NOT introduce React, Next.js, Vue, Angular, Svelte, a custom JavaScript build chain, or a proprietary UI framework.

### R-UI-002 Navigation

WHEN the app starts  
THE SYSTEM SHALL show a sidebar navigation with at least:

- Start
- Neues Sparring
- Meine Runs
- Board-Bibliothek
- Hilfe / Leitplanken

Admin navigation MAY be shown only if the current user has an admin role.

### R-UI-003 Start page

WHEN a user opens the start page  
THE SYSTEM SHALL show:

- product title,
- short value proposition,
- compliance hints,
- use-case entry points,
- recent runs if available.

### R-UI-004 Use-case entry points

WHEN a user selects a use-case entry point  
THE SYSTEM SHALL store the selected use case in `st.session_state`  
AND navigate or route the user into the guided sparring flow.

### R-UI-005 Mock mode visibility

WHEN no `BOARD_API_BASE_URL` is configured  
THE SYSTEM SHALL run in mock mode  
AND visibly indicate that no real backend run is being executed.

---

## 4. Guided sparring flow requirements

### R-FLOW-001 Wizard steps

THE SYSTEM SHALL implement the guided sparring flow with the following MVP steps:

1. Use case selection.
2. Context entry.
3. Safety assessment.
4. Prompt coach review.
5. Board and output format confirmation.
6. Run execution and result display.

### R-FLOW-002 Session state

WHEN the user moves between wizard steps  
THE SYSTEM SHALL preserve the selected use case, context values, safety result, prompt draft, board template and output format in `st.session_state`.

### R-FLOW-003 Back navigation

WHEN the user is in a later wizard step  
THE SYSTEM SHOULD allow returning to previous steps without losing already entered data.

### R-FLOW-004 Context validation

WHEN the user submits context  
THE SYSTEM SHALL block progression if the primary question or goal field is empty.

WHEN context text is shorter than 50 characters  
THE SYSTEM SHOULD warn the user that the result may be generic, but progression MAY remain possible.

---

## 5. Use-case template requirements

### R-TPL-001 Required use cases

THE SYSTEM SHALL provide at least these use cases:

- `decision_brief`
- `communication_review`
- `project_structuring`
- `risk_challenge`
- `strategy_sparring`
- `concept_challenge`

### R-TPL-002 Use-case fields

EACH use case template SHALL contain:

- key,
- title,
- description,
- recommended board key,
- recommended output format key,
- context field list.

### R-TPL-003 Referential integrity

FOR EACH use case template  
THE SYSTEM SHALL ensure that the recommended board key exists in the board template registry  
AND the recommended output format key exists in the output format registry.

---

## 6. Safety assessment requirements

### R-SAFE-001 Safety levels

THE SYSTEM SHALL classify user input into exactly one of these levels:

- `green`
- `yellow`
- `red`

### R-SAFE-002 Green behavior

WHEN the safety level is `green`  
THE SYSTEM SHALL allow the user to proceed without additional confirmation.

### R-SAFE-003 Yellow behavior

WHEN the safety level is `yellow`  
THE SYSTEM SHALL show the reasons for the classification  
AND require explicit user confirmation before enabling run start.

### R-SAFE-004 Red behavior

WHEN the safety level is `red`  
THE SYSTEM SHALL disable or block run start by default  
AND show anonymization or removal guidance.

### R-SAFE-005 IBAN detection

WHEN input contains an IBAN-like pattern  
THE SYSTEM SHALL classify safety as `red`.

### R-SAFE-006 E-mail detection

WHEN input contains an e-mail-like pattern  
THE SYSTEM SHALL classify safety as `red` unless explicitly overridden by future governance rules.

### R-SAFE-007 Customer data keywords

WHEN input contains customer-number, account-number or personal-data keywords  
THE SYSTEM SHALL classify safety as `red` or stronger than `yellow`.

### R-SAFE-008 Internal business keywords

WHEN input contains internal business keywords such as strategy, board, budget, margin, contribution margin or confidential  
THE SYSTEM SHOULD classify safety as at least `yellow` unless red signals are present.

### R-SAFE-009 Local MVP

FOR MVP  
THE SYSTEM SHALL implement safety assessment locally in Streamlit as deterministic rule-based logic.

Future backend persistence MAY be implemented later.

---

## 7. Prompt coach requirements

### R-PC-001 Rule-based MVP

FOR MVP  
THE SYSTEM SHALL generate the improved prompt locally using deterministic templates and the structured context.

### R-PC-002 Editable prompt

WHEN the prompt coach generates a prompt draft  
THE SYSTEM SHALL allow the user to edit it before sending it to the board.

### R-PC-003 Transparency

WHEN the prompt draft is shown  
THE SYSTEM SHALL clearly indicate that this is the text that will be sent to the board.

### R-PC-004 Quality hints

THE SYSTEM SHOULD show short quality hints, for example missing target group, missing decision deadline, missing constraints or insufficient context.

---

## 8. Board and output format requirements

### R-BOARD-001 Required board templates

THE SYSTEM SHALL provide at least these board templates:

- `management_board`
- `banking_governance_board`
- `communication_board`
- `project_delivery_board`
- `learning_board`

### R-BOARD-002 Board template fields

EACH board template SHALL contain:

- key,
- title,
- description,
- director identifiers.

### R-OUT-001 Required output formats

THE SYSTEM SHALL provide at least these output formats:

- Executive Summary
- Entscheidungsvorlage
- Projektauftrag
- Kommunikationsentwurf
- Risiko-Log
- To-do-Plan
- One-Pager

### R-OUT-002 Defaulting

WHEN a use case is selected  
THE SYSTEM SHALL preselect the recommended board and output format.

---

## 9. Backend integration requirements

### R-BE-001 Existing endpoints first

FOR MVP  
THE SYSTEM SHALL integrate with existing backend endpoints before implementing optional new backend endpoints.

### R-BE-002 API base URL

WHEN `BOARD_API_BASE_URL` is configured  
THE SYSTEM SHALL use it as the FastAPI backend base URL.

### R-BE-003 Run start

WHEN the user starts a run  
THE SYSTEM SHALL call the existing backend run endpoint if backend mode is active.

### R-BE-004 SSE streaming

WHEN the backend stream endpoint is available  
THE SYSTEM SHOULD display director messages progressively as they arrive.

### R-BE-005 Error handling

WHEN the backend returns 401  
THE SYSTEM SHALL show a German message indicating that the session is invalid or expired.

WHEN the backend returns 403  
THE SYSTEM SHALL show a German message indicating insufficient permissions.

WHEN the backend returns 429  
THE SYSTEM SHALL show a German message indicating too many requests.

WHEN the backend returns 5xx  
THE SYSTEM SHALL show a German message indicating a temporary system error without exposing stack traces.

---

## 10. Export and result requirements

### R-EXP-001 Markdown export

WHEN a run has a result  
THE SYSTEM SHALL allow the user to download the result as Markdown.

### R-EXP-002 Export content

The Markdown export SHALL contain at minimum:

- question or prompt,
- selected use case,
- safety level,
- selected board,
- selected output format,
- synthesis or mock result,
- director contributions if available.

### R-EXP-003 Copy support

THE SYSTEM SHOULD make the final result easy to copy from the UI.

---

## 11. Azure deployment requirements

### R-AZ-001 Streamlit container

THE SYSTEM SHALL provide a Dockerfile for the Streamlit app.

### R-AZ-002 Container port

THE Streamlit container SHALL listen on port `8501`.

### R-AZ-003 Configuration

THE Streamlit container SHALL support configuration via environment variables, at minimum:

- `BOARD_API_BASE_URL`
- `APP_ENV`
- `AUTH_DEV_BYPASS`

Azure identity variables MAY be added if Entra integration is implemented in the same iteration.

### R-AZ-004 Azure Container Apps

Deployment design SHALL target Azure Container Apps.

### R-AZ-005 Secrets

Secrets SHALL be injected by Azure mechanisms such as Container App secrets, Key Vault references or managed identity. Secrets SHALL NOT be committed.

---

## 12. Testing requirements

### R-TEST-001 Template tests

THE SYSTEM SHALL include tests ensuring that all required templates exist and that use-case references are valid.

### R-TEST-002 Safety tests

THE SYSTEM SHALL include tests for green, yellow and red safety classifications.

### R-TEST-003 Prompt coach tests

THE SYSTEM SHOULD include tests ensuring that prompt drafts include the user goal, context and output format instructions.

### R-TEST-004 Renderer tests

THE SYSTEM SHOULD include tests ensuring Markdown export includes the required sections.

---

## 13. Done criteria

The implementation is done when:

1. The Streamlit app starts locally.
2. Mock mode works without backend configuration.
3. The guided sparring flow can be completed.
4. Red safety blocks run start.
5. Yellow safety requires confirmation.
6. Prompt coach creates an editable prompt draft.
7. Board and output defaults are applied from use case selection.
8. Mock result can be exported as Markdown.
9. Existing backend integration works when `BOARD_API_BASE_URL` is configured.
10. Required tests pass.
