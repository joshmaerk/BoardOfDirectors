# Personal Board of Directors

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

## Tests

```bash
pip install -e ".[dev]"
pytest -q
```

Sieben Test-Module decken Persona-Loading, Joshua-Profil-Injection, RAG-Whitelist, Archive-Format (Frontmatter, SCQA, Compliance), Memory-FIFO, Debate-Round-Flow (mit Mock-Client), Convergence-Check und Budget-Abort.

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
