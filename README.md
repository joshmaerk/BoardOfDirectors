# Personal Board of Directors

[![CI](https://github.com/joshmaerk/BoardOfDirectors/actions/workflows/ci.yml/badge.svg)](https://github.com/joshmaerk/BoardOfDirectors/actions/workflows/ci.yml)
[![Security](https://github.com/joshmaerk/BoardOfDirectors/actions/workflows/security.yml/badge.svg)](https://github.com/joshmaerk/BoardOfDirectors/actions/workflows/security.yml)

Dialogisches Sparring-System mit sechs AI-Personen, das im Terminal eine moderierte Roundtable-Debatte führt und in einer SCQA-Synthese mündet. Lokal lauffähig, Python 3.11+, Anthropic API.

> **Inspiration:** Philipp Klöckner, OMR 2026 ("AI Council Pattern").

---

## Compliance-Hinweis (bitte zuerst lesen)

Dieses Tool ist agnostisch konzipiert. Es enthält keine Mechanismen, die per se gegen interne Datenschutz- oder IT-Sicherheitsrichtlinien einer Arbeitgeber-Institution verstoßen, **trifft aber auch keine Vorkehrungen für deren Einhaltung**.

Die Freigabe für Konzern-Themen (DSGVO, DORA, interne IT-Policies, Verarbeitung personenbezogener Daten, Geschäftsgeheimnisse) klärt der Nutzer eigenverantwortlich mit der zuständigen IT, dem DPO und ggf. dem Datenschutzbeauftragten. Jeder Archiv-File enthält im Frontmatter `compliance_status: "user-responsibility"`.

API-Calls gehen an die Anthropic-Cloud (Standard-Endpoint). Vault-Notizen werden zur Laufzeit aus dem lokalen Filesystem gelesen und können als Teil der Prompts an die API übertragen werden. Die Whitelist in `config.yaml:obsidian.allowed_subfolders` ist deine erste Verteidigungslinie - prüfe sie.

---

## Die sechs Personen

| Persona | Rolle |
|---|---|
| Der Stratege | McKinsey/BCG-Style, denkt in Optionen, eröffnet mit Reframing |
| Der CFO-Skeptiker | Konservativer Finanzvorstand, fordert Zahlen und Business Case |
| Der Banking Veteran | 30 Jahre ECB-supervised Banking, Aufsichtsrecht, Sektorlogik |
| Der Devil's Advocate | Strukturierter Querdenker, sucht blinde Flecken |
| Der Communications Coach | Senior Communications Advisor, Stakeholder-Politik, Bericht-Ton |
| Der Moderator | Conductor, neutral, schließt mit SCQA-Briefing |

Die Persona-Definitionen liegen als portable Markdown-Files in `.claude/agents/*.md` (Format: native Claude Code Subagents). Der Python-Conductor liest den Body als System-Prompt und ruft die Anthropic API direkt - volle Kontrolle über Round-Logik, Token-Budget, Streaming und Convergence-Check.

---

## Roundtable-Ablauf

```
Moderator-Opening (1-2 Sätze, framet die Frage)
        ↓
Round 1 - Opening Statements (parallel, je 2-4 Sätze)
        ↓
Round 2 - Reaction Round (sequenziell, Devil's Advocate explizit angetriggert)
        ↓
Convergence-Check (optional, Moderator-LLM-Call + click.confirm)
        ↓
Round 3 - Final Position (parallel, je ein Satz)
        ↓
Round 4 - Moderator-Synthese (SCQA + Empfehlung)
        ↓
Archiv-File (Markdown)
```

---

## Setup

```bash
# 1. Repo clonen
git clone <repo-url> board-of-directors
cd board-of-directors

# 2. Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install
pip install -e .

# 4. API-Key konfigurieren
cp .env.example .env
# Editor öffnen, ANTHROPIC_API_KEY=... eintragen

# 5. Config konfigurieren (Vault-Pfad, Whitelist)
cp config.yaml.example config.yaml
# Editor öffnen, obsidian.vault_path und allowed_subfolders anpassen
```

`board` ist nach `pip install -e .` als Shell-Befehl verfügbar. Alternativ funktioniert `python -m conductor.cli`.

---

## Beispiel-Aufrufe

```bash
# Use Case 1: Strategische Führungsentscheidung
board ask "Wie sollte ich die VC-Integration über die nächsten sechs Monate steuern?"

# Use Case 2: Stakeholder-Kommunikation, mit Memory aus früheren Sessions
board ask "Entwurf einer E-Mail an Vorstand X zur Reorganisation" --memory

# Variante: Frage aus Datei, Personen-Filter (Moderator läuft immer mit)
board ask --topic-file ./topics/reorg-q3.md --persona-only stratege,cfo-skeptiker
```

Während der Session läuft im Terminal ein Multi-Pane-Live-Display (rich-Library): jede aktive Person hat ein eigenes Panel, der Footer zeigt Token-Auslastung in grün/gelb/rot. `Ctrl+C` bricht graceful ab und schreibt das Teil-Archiv bis zum Abbruchpunkt.

### Archiv-Verwaltung

```bash
board archive list
board archive show 2026-05-22_14-30_wie-steuere-ich-die-vc-integration.md
```

---

## Was im Archiv steht

Pro Session ein Markdown-File unter `./board-archives/` mit Frontmatter:

```yaml
date: 2026-05-22T14:30:00
topic: "VC-Integration sechs Monate"
question: "..."
use_case: "Strategische Führungsentscheidung"
personas: [stratege, cfo-skeptiker, banking-veteran, devils-advocate, comms-coach, moderator]
memory_loaded: false
tokens_input: 4521
tokens_output: 12843
budget_status: "grün"
duration_seconds: 87
compliance_status: "user-responsibility"
aborted: false
```

Body enthält Moderator-Opening, drei Substanz-Runden, SCQA-Synthese mit Empfehlung, sowie die Liste aller gelesenen Obsidian-Notizen.

---

## Memory (optional, opt-in pro Session)

Mit `--memory` werden die letzten Einträge pro Persona aus `./board-archives/.memory/{persona}.json` in den jeweiligen System-Prompt injiziert. Nach der Session wird die finale Position jeder Person als neuer Eintrag angehängt. FIFO-Cap default 50 Einträge.

---

## Config-Referenz

| Pfad | Default | Bedeutung |
|---|---|---|
| `api.model` | `claude-opus-4-7` | Anthropic-Modell |
| `obsidian.vault_path` | - | Absoluter Pfad zum Obsidian-Vault |
| `obsidian.allowed_subfolders` | - | Whitelist für RAG-Zugriff |
| `obsidian.excluded_patterns` | - | Glob-Patterns die zusätzlich blocken |
| `debate.token_budget_total` | 80000 | Output-Token-Budget pro Session (graceful abort bei Überschreitung) |
| `debate.token_budget_per_persona.opening` | 400 | max Tokens für R1-Beiträge |
| `debate.token_budget_per_persona.reaction` | 300 | max Tokens für R2 |
| `debate.token_budget_per_persona.final` | 150 | max Tokens für R3 |
| `debate.moderator_synthesis_tokens` | 1200 | max Tokens für SCQA-Synthese |
| `debate.convergence_detection` | true | Moderator-Check nach R2, ob R3 übersprungen werden kann |
| `memory.max_entries_per_persona` | 50 | FIFO-Cap der Memory-Files |

---

## Development

```bash
pip install -e ".[dev]"
pre-commit install

# Lint + Format + Type-Check (alle drei laufen in CI)
ruff check .
ruff format --check .
python -m mypy conductor

# Tests mit Coverage-Threshold (CI gate: 80%)
python -m pytest --cov=conductor --cov-report=term-missing --cov-fail-under=80

# Security-Gates (laufen auch in der CI)
bandit -r conductor -ll
pip-audit -r requirements.txt
```

### CI-Pipeline

Zwei GitHub-Actions-Workflows laufen auf jedem Push und Pull-Request:

| Workflow | Jobs |
|---|---|
| `ci.yml` | Ruff lint + format check + mypy, Pytest auf Python 3.11/3.12/3.13 Matrix, Coverage-Gate >= 80% |
| `security.yml` | Bandit (SAST, SARIF-Upload nach Code-Scanning), pip-audit (Dependency-Vulnerabilities), gitleaks (Secret-Scanning); zusätzlich wöchentlich Montag 04:00 UTC |
| `streamlit-ci.yml` | Ruff lint + format check, Pytest Unit-Tests (7 Module), Playwright E2E-Tests (4 Dateien, Chromium), Screenshot-Upload als CI-Artifact |

Dependabot prüft wöchentlich `pip`- und `github-actions`-Updates.

### Tests

Acht Test-Module decken: Persona-Loading + Joshua-Profil-Injection, YAML-Config, RAG-Whitelist, Archive-Format (Frontmatter, SCQA, Compliance), Memory-FIFO, Token-Ledger + Budget-Abort, Debate-Round-Flow (mit Mock-Client) + Convergence-Check + Keyboard-Interrupt, Session-Runner (mit Mock-Client), CLI-Smoke (CliRunner), Streaming-Pane-Modell.

**Streamlit-App (`streamlit_app/tests/`):** Sieben Unit-Test-Module (auth, api_client, prompt_coach, renderers, safety, state, templates) und vier Playwright-E2E-Module (Start-Seite, Wizard Golden-Path, Safety-Klassifikation Rot/Gelb, Board-Bibliothek + Hilfe). E2E-Tests laufen gegen eine gestartete App im Mock-Modus; Screenshots landen in `docs/screenshots/` und werden als CI-Artifact gespeichert.

---

## Troubleshooting

- **`Config file not found`** - du hast `config.yaml.example` nicht nach `config.yaml` kopiert oder bist im falschen Verzeichnis.
- **`ANTHROPIC_API_KEY missing`** - `.env` fehlt oder enthält keinen Wert. `load_dotenv()` läuft beim CLI-Start.
- **Live-Display flackert / wirkt komisch in IDE-Terminal** - mit `--no-stream` deaktivieren.
- **`[blocked: path '...' is outside the whitelisted vault scope]`** in den Personen-Antworten - die Person hat versucht eine Notiz außerhalb der Whitelist zu lesen. Funktioniert wie erwartet.
- **Token-Budget zu früh "rot"** - `debate.token_budget_total` in `config.yaml` hochsetzen, oder per-persona-Limits senken.

---

## Out of Scope (V1)

Web-UI, Voice-Input, Embedding-RAG, Persona-Dynamik zur Laufzeit, Multi-User, Cloud-Deployment, native Subagent-Invocation als Default-Pfad (die `.md`-Files sind dafür aber kompatibel).

---

# Backend API für Streamlit (`app/`)

Neben dem `conductor/`-CLI liegt im Repo ein eigenständiges **FastAPI-Backend**
unter `app/`, das von der bestehenden Streamlit-App (mit Entra/Azure-AD-Auth)
angesprochen wird. Multi-User, DB-persistent, Multi-Provider.

## Stack

- Python 3.11+, FastAPI, Pydantic v2
- SQLAlchemy 2 (async) + asyncpg + Alembic
- Provider via `LLMClient`-Protocol:
  - **Azure OpenAI** (`openai`-SDK im Azure-Modus)
  - **Azure AI Foundry** für Claude-Modelle (`azure-ai-inference` SDK,
    Managed-Identity oder Key)
- Entra (Azure AD) JWT-Validierung via JWKS
- SSE-Live-Stream der Director-Messages während eines Runs

## Local development

```bash
cp .env.example .env
# Für lokale Iteration ohne echten Tenant:
#   AUTH_DEV_BYPASS=true
docker compose up --build
# API auf http://localhost:8000  ·  OpenAPI auf /docs
```

Migrations manuell:

```bash
alembic upgrade head
```

## API-Endpoints (v1)

Alle unter `/api/v1`, alle protected per `Authorization: Bearer <entra-token>`
außer `/healthz`.

- `GET /healthz`
- `GET /me`
- `GET/POST /directors` · `GET/PUT/DELETE /directors/{id}`
- `GET/POST /boards` · `GET/PUT/DELETE /boards/{id}`
- `POST /boards/{id}/runs` — startet einen Run (async, Antwort sofort)
- `GET /runs/{id}` — Status + alle Messages
- `GET /runs/{id}/messages`
- `POST /runs/{id}/cancel`
- `GET /runs/{id}/stream` — Server-Sent Events mit Live-Director-Messages

OpenAPI-Schema unter `/openapi.json`.

## Streamlit-Integration

Die Streamlit-App reicht das Entra-Access-Token im `Authorization`-Header weiter.
Das Backend validiert es gegen Entra-JWKS, extrahiert `oid` (stabile User-ID)
und nutzt diese für Ownership/Authorization.

## Konfiguration (Auszug)

Siehe `.env.example`. Wichtigste Variablen:

- `AZURE_TENANT_ID`, `AZURE_API_AUDIENCE` — Entra-Validierung
- `AZURE_OPENAI_*` — Endpoint, Key, Deployment-Map
- `AZURE_AI_FOUNDRY_*` — Endpoint, Key oder Managed-Identity, Deployment-Map (Claude)
- `LLM_PROVIDER_MAP` — Modellname-Präfix → Provider-ID
- `DATABASE_URL` — async Postgres URL (`postgresql+asyncpg://...`)
- `ALLOWED_ORIGINS` — kommagetrennte Liste (Streamlit-Origin)
- `AUTH_DEV_BYPASS` — nur lokal, akzeptiert jeden Request als Fake-User

## Mehr Doku

- [`docs/architecture.md`](docs/architecture.md) — System-Layout, Datenfluss, Provider-Routing.
- [`docs/runbook.md`](docs/runbook.md) — On-Call: Logs lesen, Worker bouncen, Postgres-Failover, DSGVO-Requests.
- [`docs/streamlit-integration.md`](docs/streamlit-integration.md) — Code-Beispiel für den Streamlit-Client (Token-Forwarding, SSE-Stream).
- [`infra/main.bicep`](infra/main.bicep) — Azure IaC für Container Apps + Postgres + Redis + Key Vault + App Insights.

---

# Streamlit WebUI (`streamlit_app/`)

Die Streamlit-WebUI ermöglicht internen Nutzern geführten Zugang zum Board-of-Directors-System ohne CLI-Kenntnisse.

## Seiten

| Seite | Inhalt |
|---|---|
| `01_Start.py` | Willkommensseite, Sicherheitshinweise, 6 Use-Case-Einstiegsbuttons |
| `02_Neues_Sparring.py` | 6-stufiger Wizard: Use Case → Kontext → Safety-Check → Prompt-Review → Board/Format → Ergebnis + Markdown-Download |
| `03_Meine_Runs.py` | Run-Verlauf der aktuellen Sitzung |
| `04_Board_Bibliothek.py` | Übersicht aller Board- und Use-Case-Templates |
| `05_Hilfe_Leitplanken.py` | Safety-Level-Erläuterungen (Grün/Gelb/Rot) mit Beispielen |

## Komponenten (`streamlit_app/components/`)

| Modul | Aufgabe |
|---|---|
| `state.py` | Session-State initialisieren, Wizard-Reset |
| `safety.py` | Lokale Safety-Klassifikation ohne LLM-Call (Grün/Gelb/Rot) |
| `prompt_coach.py` | Prompt-Aufbau aus Use-Case-Template und Kontext |
| `api_client.py` | HTTP-Client gegen FastAPI-Backend + deterministischer `MockBoardApiClient` |
| `templates.py` | Frozen-Dataclass-Registry für Boards, Use Cases und Output-Formate |
| `renderers.py` | Markdown-Export-Aufbau für das Ergebnis-Download |
| `auth.py` | Bearer-Token aus `st.session_state["entra_access_token"]` lesen |

## Lokaler Mock-Modus (kein Backend erforderlich)

```bash
pip install -r streamlit_app/requirements.txt
streamlit run streamlit_app/app.py
```

Die App startet unter `http://localhost:8501`. Ohne `BOARD_API_BASE_URL` ist der Mock-Modus aktiv – alle Ergebnisse sind synthetische Beispiele.

## Lokaler Backend-Modus

```bash
export BOARD_API_BASE_URL=http://localhost:8000
streamlit run streamlit_app/app.py
```

## Wichtige Umgebungsvariablen

| Variable | Pflicht | Beschreibung |
|---|---|---|
| `BOARD_API_BASE_URL` | Nein | Backend-URL. Fehlt → Mock-Modus aktiv. |
| `AUTH_DEV_BYPASS` | Nein | `true` deaktiviert Token-Prüfung lokal. |
| `AZURE_TENANT_ID` | Nein | Für künftige Entra-OAuth-Integration. |
| `AZURE_CLIENT_ID` | Nein | App-Registration-Client-ID für OAuth. |
| `AZURE_API_SCOPE` | Nein | API-Scope für Bearer-Token-Anforderung. |

## Docker

```bash
docker build -f streamlit_app/Dockerfile -t bod-streamlit:latest .
docker run -p 8501:8501 bod-streamlit:latest
```

## Azure Deployment

Siehe [`docs/streamlit-azure-deployment.md`](docs/streamlit-azure-deployment.md) für vollständige Deployment-Anleitung inkl. ACR-Push und Bicep-Parametrisierung.

## Bekannte Einschränkungen

- **Session-State**: Pro Browser-Tab. Wizard-Daten gehen bei App-Neustart verloren.
- **Run-Verlauf**: Nur sitzungslokal (`st.session_state`). Persistenz erfordert einen Backend-Endpunkt (noch nicht implementiert).
- **Entra-OAuth**: Nicht implementiert. Lokal: `AUTH_DEV_BYPASS=true`. Produktion: Bearer-Token muss extern bereitgestellt werden.
- **Admin-Seite**: `06_Admin.py` ist nicht implementiert (außerhalb MVP-Scope).

