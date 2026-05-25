# Changelog

Alle wesentlichen Änderungen werden hier festgehalten.
Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

---

## [Unveröffentlicht] — PR #17

### Fixed
- `start_run` sendete `"question"` statt `"input"` → HTTP 422 bei jedem Live-Run
- `get_run` las falsches Feld `"question"` statt `"input"` und `"synthesis"` statt `"result_summary"`
- SSE-Parser brach bei leerem `data:`-Keepalive vorzeitig ab statt fortzufahren
- `event: error`-Frames wurden still ignoriert; Spinner hing unbegrenzt
- Sprecher-Label zeigte Enum-String `"director"` statt Persona-Name
- `mock_mode` in Session-State wurde nie mit `is_mock_mode()` synchronisiert → Live-Modus wurde fälschlich als Mock angezeigt
- Ausgabeformat-Änderung in Schritt 5 löste keinen Prompt-Rebuild aus → falsches Format im übermittelten Prompt
- `dict.get("messages", fallback)` ignorierte leere Liste → gestreamte Nachrichten gingen verloren
- Kein Guard vor `start_run` bei leerem Prompt → stille Übermittlung einer leeren Frage

### Added
- `persona_name`-Feld in `DirectorMessageOut`-Schema und SSE-Endpoint (Director-Lookup aus DB)
- `_role_label()`-Fallback für Enum-Werte ohne DB-Persona (`"synthesis"` → `"Moderator"`)

---

## [2026-05-25] — PR #16

### Added
- Playwright E2E-Tests und UI-Dokumentations-Screenshots (`docs/screenshots/`)
- Unit-Tests für `api_client`, `state` und `auth`
- Azure IaC für Streamlit Container App (`infra/main.bicep`)
- Streamlit Docker-Packaging (`streamlit_app/Dockerfile`, `.dockerignore`)
- Deployment-Dokumentation (`docs/streamlit-azure-deployment.md`)

### Fixed
- Fehlerbehandlung in Wizard-Schritt 6 (Error-State und Rücknavigation)
- Drei CI-Fehler im E2E-Job
- Ruff-Lint-Issues in `streamlit_app`

---

## [2026-05-25] — PR #15 / #14

### Added
- `GET /api/v1/runs` — persistente Run-History im Backend
- Run-History-Seite (`pages/03_Meine_Runs.py`) mit Echtdaten-Fallback auf Mock

---

## [2026-05-25] — PR #13 / #12

### Added
- Streamlit-Gerüst mit Session-State-Management (`app.py`, `components/state.py`)
- Deterministische Sicherheitsprüfung (`components/safety.py`) mit Tests
- Lokaler Prompt-Coach (`components/prompt_coach.py`) mit Tests
- Template-Registry für Use-Cases, Boards und Ausgabeformate (`components/templates.py`) mit Tests
- Markdown-Renderer und Export-Funktion (`components/renderers.py`) mit Tests
- Mock-API-Client für lokale Entwicklung ohne Backend-Konfiguration
- Geführter 6-Schritte-Sparring-Wizard (`pages/02_Neues_Sparring.py`)
- Board-Bibliothek-Seite (`pages/04_Board_Bibliothek.py`)
- Hilfe- und Leitplanken-Seite (`pages/05_Hilfe_Leitplanken.py`)
- Streamlit CI-Workflow (`.github/workflows/streamlit-ci.yml`)

---

## [2026-05-25] — PR #4

### Changed
- GitHub Actions `codeql-action` von v3 auf v4 aktualisiert (Dependabot)

---

## [Initial Release] — PR #1

### Added
- Personal Board of Directors V1: FastAPI-Backend, Conductor-CLI, sechs AI-Personas
- CI/CD-Pipeline: Lint, Typecheck, Test-Matrix (Python 3.11–3.13), Security-Scans
- Pre-commit Hooks und Dependabot-Konfiguration
- Vollständige Projektdokumentation (README, ADRs, Runbooks, Specs)
