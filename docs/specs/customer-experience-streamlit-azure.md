# Spec: Customer-Experience-orientierte WebUI fuer BoardOfDirectors

Status: Draft fuer Coding Agent  
Ziel-Branch: `main` oder Feature-Branch `feature/cx-streamlit-azure`  
Zielgruppe der Umsetzung: Coding Agent / AI Coding Agent  
Produktziel: Interne Mitarbeitende mit niedrigem KI-Reifegrad sicher, gefuehrt und nutzenorientiert in KI-gestuetzte Expertenarbeit bringen.

---

## 1. Executive Summary

`BoardOfDirectors` soll von einem technisch geprägten Multi-Agent-/Board-System zu einem gefuehrten internen KI-Sparring-Produkt weiterentwickelt werden.

Die WebUI ist strikt mit generischem Streamlit umzusetzen. Keine Custom-Frontend-Frameworks, kein React, kein Next.js, kein separates SPA. Die bestehende FastAPI-Backend-Architektur bleibt fuehrend. Deployment-Ziel ist Azure.

Der primaere interne Kunde ist kein Prompt-Experte, sondern ein Fachuser, Projektleiter oder Fuehrungskraft, der komplexe Expertenarbeit mit KI schrittweise produktiver machen soll.

Kernversprechen:

> In wenigen Minuten ein belastbares KI-Sparring erhalten: gefuehrt, sicher, nachvollziehbar und als konkretes Arbeitsprodukt verwendbar.

---

## 2. Nicht-Ziele / Constraints

### 2.1 Harte Constraints

1. WebUI strikt mit generischem Streamlit.
2. Keine proprietäre UI-Komponentenbibliothek, kein komplexes Frontend-Build-System.
3. Backend bleibt FastAPI-basiert.
4. Deployment in Azure-Umgebung.
5. Authentifizierung ueber Entra ID / Azure AD Token Forwarding, sofern in Zielumgebung verfuegbar.
6. Keine direkte Speicherung von API Keys im Code oder Streamlit-Repo.
7. Compliance- und Datenschutzhinweise muessen im Nutzerfluss sichtbar sein, nicht nur in Dokumentation.

### 2.2 Nicht-Ziele fuer diese Spec

- Kein vollstaendiges DLP-System mit garantierter Erkennung aller personenbezogenen Daten.
- Kein Voice Interface.
- Kein Multi-Tenant Admin-Portal ueber Streamlit hinaus.
- Kein Ersatz fuer zentrale KI-Governance.
- Kein Custom Design System.

---

## 3. Zielnutzer und Jobs-to-be-done

### 3.1 Primaere Personas

| Persona | Ausgangslage | Job-to-be-done |
|---|---|---|
| KI-Einsteiger / Fachexperte | Wenig Prompt-Erfahrung, fachlich stark | Gute Frage strukturieren und verwertbares Ergebnis erhalten |
| Projektleiter | Komplexe Vorhaben, viele Stakeholder | Projektauftrag, Risiken, Entscheidungsbedarf schaerfen |
| Fuehrungskraft | Wenig Zeit, hoher Entscheidungsdruck | Optionen, Trade-offs, Vorstandssprache, Kommunikationslinien erhalten |
| AI Champion | Fortgeschritten | Boards und Templates wiederverwenden und weiterentwickeln |
| Compliance / IT | Governance-Interesse | Nutzung nachvollziehbar, sicher und kontrollierbar halten |

### 3.2 Haupt-Jobs

1. Entscheidung vorbereiten.
2. Kommunikation formulieren oder verbessern.
3. Projekt strukturieren.
4. Risiken und blinde Flecken erkennen.
5. Strategieoptionen bewerten.
6. Fachkonzept challengen.
7. KI-Kompetenz durch Nutzung aufbauen.

---

## 4. Ziel-Journey

### 4.1 Soll-Ablauf fuer normalen User

1. User oeffnet Streamlit-App.
2. User sieht Use-Case-Kacheln statt leerem Chatfeld.
3. User waehlt Arbeitsanlass.
4. System fuehrt durch Kontextfelder.
5. Safety Check bewertet Eingabe mit Ampel.
6. Prompt Coach schlaegt verbesserte Fragestellung vor.
7. System empfiehlt Board Template und Output Format.
8. User startet Run.
9. UI zeigt Live-Fortschritt und Director-Beitraege.
10. User erhaelt Ergebnis als Arbeitsprodukt.
11. User bewertet Ergebnis und kann es speichern/exportieren.
12. System zeigt kurzen Lernhinweis zur Prompt-Qualitaet.

### 4.2 UX-Prinzipien

- Fuehren statt erklaeren.
- Wenige Entscheidungen pro Screen.
- Fachsprache, aber kein technischer Jargon fuer Enduser.
- Default Templates vor freier Konfiguration.
- Safety by default.
- Ergebnis als Arbeitsprodukt, nicht nur als Chat-Protokoll.
- Lernen im Arbeitsfluss, nicht als separates Training.

---

## 5. Streamlit-WebUI: Seitenstruktur

Alle Seiten sind generisch mit Streamlit umzusetzen. Nutze native Streamlit-Elemente wie `st.set_page_config`, `st.sidebar`, `st.tabs`, `st.expander`, `st.form`, `st.columns`, `st.status`, `st.progress`, `st.spinner`, `st.toast`, `st.dataframe`, `st.download_button`.

### 5.1 App-Struktur

Empfohlener Pfad:

```text
streamlit_app/
  app.py
  pages/
    01_Start.py
    02_Neues_Sparring.py
    03_Meine_Runs.py
    04_Board_Bibliothek.py
    05_Admin.py
  components/
    api_client.py
    auth.py
    safety.py
    templates.py
    renderers.py
    state.py
  tests/
    test_templates.py
    test_safety.py
```

Alternative: Falls bereits eine Streamlit-App existiert, integriere diese Struktur dort, aber halte die Module getrennt.

### 5.2 Navigation

Sidebar:

- Start
- Neues Sparring
- Meine Runs
- Board-Bibliothek
- Hilfe / Leitplanken
- Admin, nur falls Rolle vorhanden

### 5.3 Startseite

Ziel: Orientierung und schneller Einstieg.

Elemente:

1. Titel: `Board of Directors - KI-Sparring fuer Expertenarbeit`
2. Kurzer Nutzenclaim.
3. Drei Hinweise:
   - Keine Kundendaten eingeben.
   - Interne/vertrauliche Inhalte nur gemaess Governance.
   - Ergebnis ist Sparring, keine automatische Entscheidung.
4. Use-Case-Kacheln als Buttons:
   - Entscheidung vorbereiten
   - Kommunikation verbessern
   - Projekt strukturieren
   - Risiko challengen
   - Strategie sparren
   - Fachkonzept challengen
5. Letzte Runs als Tabelle.

Akzeptanzkriterien:

- User kann von Startseite mit einem Klick in `Neues Sparring` mit vorausgewaehltem Use Case wechseln.
- Keine technische Board-Konfiguration auf der Startseite.

---

## 6. Neues Sparring: Guided Flow

### 6.1 Implementierung als Streamlit Wizard

Da Streamlit keine native Multi-Step-Wizard-Komponente braucht, nutze `st.session_state["wizard_step"]`.

Schritte:

1. Use Case waehlen.
2. Kontext erfassen.
3. Safety Check.
4. Prompt Coach.
5. Board und Output Format bestaetigen.
6. Run starten und Live-Ergebnis anzeigen.

### 6.2 Step 1: Use Case

Use Cases als statische Templates in `streamlit_app/components/templates.py`.

Datenstruktur:

```python
USE_CASE_TEMPLATES = {
    "decision_brief": {
        "title": "Entscheidung vorbereiten",
        "description": "Optionen, Trade-offs, Empfehlung und Entscheidungsbedarf strukturieren.",
        "recommended_board": "management_board",
        "recommended_output": "decision_brief",
        "context_fields": ["ziel", "ausgangslage", "optionen", "restriktionen", "entscheidungsfrist"]
    },
    ...
}
```

Pflicht-Use-Cases:

- `decision_brief`
- `communication_review`
- `project_structuring`
- `risk_challenge`
- `strategy_sparring`
- `concept_challenge`

### 6.3 Step 2: Kontext erfassen

Pflichtfelder je nach Use Case:

Allgemeine Felder:

- Ziel / Fragestellung
- Kontext / Ausgangslage
- Zielgruppe des Ergebnisses
- Restriktionen / Leitplanken
- Gewuenschtes Ergebnisformat
- Dringlichkeit / Entscheidungsfrist

Validierung:

- Ziel / Fragestellung darf nicht leer sein.
- Kontext sollte mindestens 50 Zeichen haben; darunter Warnung, aber kein Block.
- Bei sensiblen Keywords Warnung im naechsten Safety Step.

### 6.4 Step 3: Safety Check

Implementiere einen einfachen regelbasierten Safety Check in Streamlit und optional zusaetzlich im Backend.

Ampeln:

- `green`: unkritisch oder allgemein.
- `yellow`: intern/vertraulich moeglich.
- `red`: personenbezogen, Kundendaten, Kontodaten, Geheimnisse oder eindeutige Datenrisiken.

Heuristische Keyword-Erkennung:

Red flags:

- IBAN
- Konto
- Kundennummer
- Sozialversicherungsnummer
- Telefonnummer
- E-Mail-Adresse
- Geburtsdatum
- Kreditvertrag
- personenbezogen
- Mitarbeiterbeurteilung mit Namen
- Gehalt

Yellow flags:

- Vorstand
- intern
- vertraulich
- Strategie
- Projektname
- Budget
- Marge
- DB
- Kundensegment
- Bank

Akzeptanzkriterien:

- Red blockiert den Run standardmaessig.
- User erhaelt anonymisierte Formulierungshinweise.
- Yellow verlangt bewusste Bestaetigung per Checkbox.
- Green erlaubt Fortsetzung.
- Safety-Ergebnis wird in Run-Metadaten oder lokalem UI-State gespeichert.

### 6.5 Step 4: Prompt Coach

Ziel: Aus den Kontextfeldern eine bessere Arbeitsfrage formulieren.

MVP-Variante:

- Prompt Coach wird lokal regelbasiert aus Template erzeugt.
- Kein eigener LLM-Call notwendig fuer MVP.

Beispiel-Output:

```text
Analysiere folgende Fragestellung aus Sicht eines Management-Sparrings:

Ziel: ...
Ausgangslage: ...
Restriktionen: ...
Zielgruppe: ...
Erwuenschtes Ergebnis: ...

Liefere: 1) Reframing, 2) Optionen, 3) Risiken, 4) Empfehlung, 5) naechste Schritte.
```

Optional spaeter:

- Backend-Endpunkt `/api/v1/prompt-coach/improve`.
- LLM-basierte Verbesserung mit Safety-Guardrails.

Akzeptanzkriterien:

- User kann den Vorschlag editieren.
- User sieht klar: „Das wird an das Board gesendet.“
- User kann zur Kontext-Erfassung zurueckspringen.

### 6.6 Step 5: Board und Output Format

Pflicht-Boards:

```python
BOARD_TEMPLATES = {
    "management_board": {
        "title": "Management Board",
        "directors": ["stratege", "cfo_skeptiker", "devils_advocate", "moderator"],
        "description": "Fuer Entscheidungen, Optionen, Trade-offs und Management-Empfehlungen."
    },
    "banking_governance_board": {
        "title": "Banking Governance Board",
        "directors": ["banking_veteran", "cfo_skeptiker", "devils_advocate", "moderator"],
        "description": "Fuer regulierte Bankthemen, Governance, Risiken und Sektorlogik."
    },
    "communication_board": {
        "title": "Communication Board",
        "directors": ["communications_coach", "devils_advocate", "stratege", "moderator"],
        "description": "Fuer Stakeholder-Kommunikation, Tonalitaet und Klarheit."
    },
    "project_delivery_board": {
        "title": "Project Delivery Board",
        "directors": ["stratege", "cfo_skeptiker", "devils_advocate", "moderator"],
        "description": "Fuer Projektauftrag, Scope, Risiken, Roadmap und Umsetzung."
    },
    "learning_board": {
        "title": "Learning Board",
        "directors": ["moderator", "stratege", "devils_advocate"],
        "description": "Fuer KI-Einsteiger mit Fokus auf Verstaendlichkeit und Lerntransfer."
    }
}
```

Output Formate:

- Executive Summary
- Entscheidungsvorlage
- Projektauftrag
- Kommunikationsentwurf
- Risiko-Log
- To-do-Plan
- One-Pager

Akzeptanzkriterien:

- Default Board und Output Format werden automatisch aus Use Case vorbelegt.
- User kann im MVP aus einer kleinen Liste wechseln.
- Advanced Board-Konfiguration bleibt optional und nicht prominent.

### 6.7 Step 6: Run starten und Live-Ergebnis

Nutze bestehenden Backend-Client analog `docs/streamlit-integration.md`.

UI-Verhalten:

- `st.status("Board arbeitet...")`
- Fortschrittsanzeige je Round, falls Status vorhanden.
- Director Messages live rendern.
- Jede Persona in `st.expander` oder Tab.
- Moderator-Synthese oben oder am Ende hervorgehoben.
- Bei Fehlern: klare Enduser-Fehlermeldung, kein Stacktrace.

Akzeptanzkriterien:

- Run kann gestartet werden.
- UI zeigt Status pending/running/done/failed/cancelled.
- User kann Run abbrechen, sofern Backend Cancel Endpoint vorhanden ist.
- Ergebnis kann kopiert und als Markdown heruntergeladen werden.

---

## 7. Backend-Erweiterungen

Bestehende Endpunkte laut README/Docs:

- `GET /healthz`
- `GET /me`
- `GET/POST /directors`
- `GET/POST /boards`
- `POST /boards/{id}/runs`
- `GET /runs/{id}`
- `GET /runs/{id}/messages`
- `POST /runs/{id}/cancel`
- `GET /runs/{id}/stream`

### 7.1 Neue oder erweiterte Endpunkte

#### 7.1.1 Safety Assessment

`POST /api/v1/safety/assess`

Request:

```json
{
  "text": "...",
  "use_case": "decision_brief"
}
```

Response:

```json
{
  "level": "green|yellow|red",
  "reasons": ["possible_personal_data"],
  "recommendations": ["Bitte Namen und Kundennummern entfernen."],
  "can_continue": true
}
```

MVP: Kann auch nur in Streamlit lokal implementiert werden. Backend-Endpunkt ist Zielbild.

#### 7.1.2 Prompt Coach

`POST /api/v1/prompt-coach/improve`

Request:

```json
{
  "use_case": "decision_brief",
  "context": {
    "ziel": "...",
    "ausgangslage": "...",
    "restriktionen": "..."
  },
  "output_format": "decision_brief"
}
```

Response:

```json
{
  "improved_prompt": "...",
  "quality_hints": ["Zielgruppe ist klar", "Entscheidungsfrist fehlt"],
  "missing_context_questions": ["Bis wann wird die Entscheidung benoetigt?"]
}
```

MVP: lokal regelbasiert in Streamlit.

#### 7.1.3 Run Feedback

`POST /api/v1/runs/{id}/feedback`

Request:

```json
{
  "rating": "helpful|partial|not_helpful",
  "tags": ["too_generic", "actionable"],
  "comment": "optional"
}
```

Response:

```json
{"status": "ok"}
```

### 7.2 Datenmodell-Erweiterungen

Falls DB-Migrationen umgesetzt werden:

#### Tabelle `use_case_templates`

- id
- key
- title
- description
- recommended_board_key
- recommended_output_format
- is_active
- created_at
- updated_at

#### Tabelle `run_feedback`

- id
- run_id
- user_oid
- rating
- tags JSONB
- comment
- created_at

#### Tabelle `safety_assessments`

- id
- run_id nullable
- user_oid
- level
- reasons JSONB
- recommendations JSONB
- created_at

#### Tabelle `saved_run_templates`

- id
- user_oid
- title
- use_case_key
- prompt
- board_id nullable
- output_format
- created_at
- updated_at

---

## 8. Output Rendering

### 8.1 Markdown Export

Jeder Run soll als Markdown exportierbar sein.

Struktur:

```markdown
# Board of Directors Ergebnis

## Fragestellung
...

## Safety Einstufung
...

## Board
...

## Synthese
...

## Director-Beitraege
...

## Naechste Schritte
...
```

### 8.2 Arbeitsprodukt-Templates

Fuer MVP genuegt post-processing per Template ohne zusaetzlichen LLM-Call.

Output-Formate:

#### Executive Summary

- Kontext
- Kernaussage
- Empfehlung
- Risiken
- Entscheidungspunkt

#### Entscheidungsvorlage

- Situation
- Complication
- Question
- Answer
- Optionen
- Bewertung
- Empfehlung
- Entscheidungsbedarf

#### Projektauftrag

- Zielbild
- Scope
- Nicht-Scope
- Deliverables
- Meilensteine
- Risiken
- Naechste Schritte

#### Risiko-Log

Tabelle:

| Risiko | Ursache | Wirkung | Eintritt | Impact | Massnahme | Owner |

---

## 9. Azure Deployment

### 9.1 Zieltopologie

Beizubehalten bzw. zu erweitern:

- Azure Container Apps Environment
- Container App `api`
- Container App `worker`
- neue Container App `streamlit`
- Azure Postgres Flexible Server
- Azure Cache for Redis
- Azure Key Vault
- Azure Container Registry
- Application Insights / Log Analytics
- Entra ID App Registrations

### 9.2 Streamlit Container App

Container:

- Image: `bod-streamlit:<sha>`
- Port: `8501`
- External ingress: ja, wenn direkt genutzt; sonst internal hinter Reverse Proxy.
- Env Vars:
  - `BOARD_API_BASE_URL`
  - `AZURE_TENANT_ID`
  - `AZURE_CLIENT_ID`
  - `AZURE_API_SCOPE`
  - `APP_ENV`
  - `AUTH_DEV_BYPASS=false`

Secrets via Key Vault references oder Container App secrets.

### 9.3 Dockerfile fuer Streamlit

Pfad: `streamlit_app/Dockerfile`

Mindestinhalt:

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY streamlit_app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY streamlit_app/ ./streamlit_app/

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 9.4 Requirements fuer Streamlit

`streamlit_app/requirements.txt`:

```text
streamlit>=1.35
httpx>=0.27
pydantic>=2
python-dotenv>=1
msal>=1.28
```

Falls bestehende Auth-Bibliothek genutzt wird, hier ergaenzen.

### 9.5 Bicep/IaC Erweiterung

Falls `infra/main.bicep` existiert, erweitern:

- Container App `streamlit`
- Ingress 8501
- Env Vars und Secrets
- Managed Identity falls noetig
- App Insights env
- ACR Pull Role

Akzeptanzkriterien:

- `azd up` oder bestehender Deploymentpfad erzeugt API, Worker und Streamlit-App.
- Streamlit kann Backend erreichen.
- Healthcheck fuer Streamlit vorhanden.
- Logs landen in Log Analytics.

---

## 10. Security und Compliance

### 10.1 UI-Leitplanken

Pflicht:

- Hinweis auf keine personenbezogenen Kundendaten.
- Safety Check vor Run.
- Yellow Checkbox.
- Red Block.
- Kein Anzeigen von technischen Secrets.

### 10.2 Backend-Leitplanken

Empfohlen:

- Request Size Limit.
- Audit Event fuer Run Start.
- Safety Assessment speichern.
- Authz auf User-Ressourcen.
- Kein Loggen vollstaendiger Prompts in technischen Logs, falls vertrauliche Inhalte moeglich sind.

### 10.3 Rollen

MVP:

- `board.user`
- `board.admin`

Optional:

- `board.champion`
- `board.compliance_reader`

---

## 11. Coding-Agent-Arbeitsplan

### Phase 1: Spec-konforme Streamlit MVP UI

Tasks:

1. Ordner `streamlit_app/` anlegen.
2. `app.py` mit Navigation und Session State anlegen.
3. `components/templates.py` mit Use Cases, Board Templates und Output Formats erstellen.
4. `components/safety.py` mit regelbasierter Ampellogik erstellen.
5. `components/api_client.py` fuer Backend Calls erstellen.
6. Seite `01_Start.py` erstellen.
7. Seite `02_Neues_Sparring.py` mit Wizard erstellen.
8. Markdown Export implementieren.
9. `requirements.txt` und Dockerfile erstellen.
10. Minimaltests fuer Safety und Templates.

Definition of Done:

- Lokal startbar mit `streamlit run streamlit_app/app.py`.
- Guided Flow funktioniert ohne Backend im Mock Mode.
- Mit `BOARD_API_BASE_URL` funktioniert echter Backend Run.
- Red Safety blockiert.
- Yellow Safety verlangt Checkbox.
- Ergebnis als Markdown downloadbar.

### Phase 2: Backend Integration

Tasks:

1. API Client gegen bestehende Endpunkte finalisieren.
2. Streaming via SSE integrieren.
3. Cancel Run Button integrieren.
4. Meine Runs anzeigen.
5. Fehlerbehandlung fuer 401/403/404/422/429/5xx.
6. Optional Feedback Endpoint implementieren.

Definition of Done:

- Live Messages werden angezeigt.
- Run Status wird korrekt dargestellt.
- User kann Ergebnisse wiederfinden.
- Fehler sind enduser-verstaendlich.

### Phase 3: Azure Deployment

Tasks:

1. Streamlit Docker Image bauen.
2. CI Workflow fuer Streamlit Image ergaenzen.
3. Azure Container App `streamlit` in IaC ergaenzen.
4. Env Vars und Secrets konfigurieren.
5. Smoke Test gegen `/healthz` oder Streamlit Root.
6. Deployment-Doku ergaenzen.

Definition of Done:

- Streamlit laeuft als Azure Container App.
- Backend API ist erreichbar.
- Auth-Konzept dokumentiert.
- Logs sichtbar.

### Phase 4: Enablement Features

Tasks:

1. Prompt Coach Hints verbessern.
2. Lernhinweis nach Run anzeigen.
3. Feedback speichern.
4. Saved Templates einfuehren.
5. Admin Board-Bibliothek anzeigen.

---

## 12. Akzeptanztests

### 12.1 Happy Path

Given ein User oeffnet die App  
When er `Entscheidung vorbereiten` waehlt  
And Kontextfelder ausfuellt  
And Safety Check gruen ist  
And Prompt bestaetigt  
Then wird ein Board Run gestartet  
And Live Messages erscheinen  
And eine Synthese ist sichtbar  
And Markdown Export ist moeglich.

### 12.2 Yellow Safety

Given ein User gibt interne Strategieinformationen ein  
When Safety Check yellow ergibt  
Then muss der User eine Checkbox bestaetigen  
Before der Run gestartet werden kann.

### 12.3 Red Safety

Given ein User gibt IBAN oder Kundennummer ein  
When Safety Check red ergibt  
Then wird der Run blockiert  
And die UI gibt Anonymisierungshinweise.

### 12.4 Backend Fehler

Given Backend liefert 401  
Then UI zeigt `Sitzung abgelaufen oder Zugriff nicht gueltig. Bitte neu anmelden.`

Given Backend liefert 429  
Then UI zeigt `Zu viele Anfragen. Bitte kurz warten und erneut versuchen.`

### 12.5 Mock Mode

Given kein `BOARD_API_BASE_URL` gesetzt ist  
Then App startet im Mock Mode  
And zeigt Demo-Ergebnisse  
And weist sichtbar auf Mock Mode hin.

---

## 13. Qualitätsstandards

- Python 3.11+.
- Type Hints fuer eigene Module.
- Keine Secrets im Repo.
- Keine personenbezogenen Testdaten.
- Ruff-kompatibler Code.
- Keine harten absoluten Pfade.
- UI-Texte auf Deutsch.
- Fehlertexte fachlich verstaendlich.
- Logging ohne Prompt-Volltext, sofern nicht explizit als sichere Debug-Option aktiviert.

---

## 14. Empfohlene erste Implementierungsreihenfolge

1. `streamlit_app/components/templates.py`
2. `streamlit_app/components/safety.py`
3. `streamlit_app/components/renderers.py`
4. `streamlit_app/components/api_client.py`
5. `streamlit_app/app.py`
6. `streamlit_app/pages/01_Start.py`
7. `streamlit_app/pages/02_Neues_Sparring.py`
8. Dockerfile und requirements
9. Tests
10. IaC-Erweiterung

---

## 15. Offene Entscheidungen

Diese Punkte soll der Coding Agent als TODO markieren, aber nicht blockieren:

1. Exakte Entra App Registration IDs.
2. Finale Azure Region.
3. Ob Streamlit extern erreichbar oder nur intern hinter Reverse Proxy laufen soll.
4. Ob Safety Assessment zunaechst nur lokal oder backendseitig persistiert wird.
5. Ob Prompt Coach im MVP regelbasiert oder LLM-basiert ist.

Default fuer MVP:

- Streamlit extern erreichbar mit Entra Auth, sofern Infrastruktur vorhanden.
- Safety lokal regelbasiert.
- Prompt Coach lokal regelbasiert.
- Backend Runs ueber bestehende API.
- Persistenz nur fuer Runs; Feedback optional.

---

## 16. Fertigstellungskriterium fuer diese Spec

Die Spec gilt als umgesetzt, wenn ein interner Fachuser ohne technische Vorkenntnisse:

1. einen Use Case auswaehlen kann,
2. durch eine strukturierte Eingabe gefuehrt wird,
3. eine Safety-Ampel sieht,
4. eine verbesserte Fragestellung bestaetigt,
5. ein empfohlenes Board startet,
6. Live-Ergebnisse sieht,
7. ein verwertbares Arbeitsprodukt exportiert,
8. und am Ende einen kurzen Lernhinweis erhaelt.
