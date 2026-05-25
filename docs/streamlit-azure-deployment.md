# Streamlit Azure Deployment

Dieses Dokument beschreibt den Betrieb der Streamlit WebUI lokal, als Docker-Container, auf Azure Container Apps und auf Azure App Service (kein Container, Linux, Python 3.11).

---

## Azure App Service (Linux, Python — empfohlen für einfaches Deployment)

### Voraussetzungen

```bash
# App Service + Service Plan anlegen (einmalig, manuell oder via IaC)
az appservice plan create \
  --name bod-streamlit-plan \
  --resource-group <rg> \
  --sku B2 \
  --is-linux

az webapp create \
  --name <app-name> \
  --resource-group <rg> \
  --plan bod-streamlit-plan \
  --runtime "PYTHON:3.11"

# Port und Startup-Kommando setzen
az webapp config appsettings set \
  --name <app-name> --resource-group <rg> \
  --settings \
    WEBSITES_PORT=8000 \
    BOARD_API_BASE_URL=https://<api-backend-fqdn>

az webapp config set \
  --name <app-name> --resource-group <rg> \
  --startup-file "python -m streamlit run app.py --server.port=8000 --server.address=0.0.0.0 --server.headless=true"
```

### CI/CD via GitHub Actions (`.github/workflows/deploy-appservice.yml`)

**Auth: Publish Profile** (einfachster Weg, kein OIDC nötig)

1. Azure Portal → App Service → Übersicht → **Veröffentlichungsprofil herunterladen**
2. Inhalt der `.PublishSettings`-Datei als GitHub Secret `AZURE_WEBAPP_PUBLISH_PROFILE` speichern
3. GitHub Variable `AZURE_WEBAPP_NAME` und `AZURE_RESOURCE_GROUP` setzen

Der Workflow deployt automatisch bei jedem Push auf `main` (nur wenn `streamlit_app/**` geändert).

**Benötigte GitHub Secrets/Variables:**

| Name | Typ | Zweck |
|------|-----|-------|
| `AZURE_WEBAPP_PUBLISH_PROFILE` | Secret | Publish-Profile-XML aus Azure Portal |
| `AZURE_CLIENT_ID` | Secret | OIDC App-ID (nur für `az`-CLI-Schritte nach Deploy) |
| `AZURE_TENANT_ID` | Secret | Entra Tenant |
| `AZURE_SUBSCRIPTION_ID` | Secret | Azure Subscription |
| `AZURE_WEBAPP_NAME` | Variable | App Service Name |
| `AZURE_RESOURCE_GROUP` | Variable | Resource Group |

### Bekannte Einschränkungen (App Service vs. Container Apps)

- Kein automatisches Scaling auf 0 (mindestens 1 Instanz läuft immer auf B-Tier)
- Kein Blue/Green-Swap ohne Deployment Slots (S1+ nötig)
- Startup-Zeit bei Cold Start ~30–60 s (Streamlit lädt beim ersten Request)

---

## Lokaler Mock-Modus

Kein Backend, kein Azure-Zugang erforderlich.

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

Die App startet unter `http://localhost:8501`.  
Mock-Modus ist aktiv, wenn `BOARD_API_BASE_URL` nicht gesetzt ist.

---

## Lokaler Backend-Modus

```bash
export BOARD_API_BASE_URL=http://localhost:8000
streamlit run streamlit_app/app.py
```

Der FastAPI-Backend-Dienst muss lokal laufen (z. B. via `docker compose up`).

---

## Umgebungsvariablen

| Variable | Pflicht | Beschreibung |
|---|---|---|
| `BOARD_API_BASE_URL` | Nein | URL des FastAPI-Backends. Fehlt sie, läuft die App im Mock-Modus. |
| `APP_ENV` | Nein | Umgebungskennung (`prod`, `staging`, `dev`). Standard: leer. |
| `AUTH_DEV_BYPASS` | Nein | `true` deaktiviert Entra-Auth lokal. Nur für Entwicklung. |
| `AZURE_TENANT_ID` | Optional | Entra-Tenant-ID für künftige OAuth-Integration. |
| `AZURE_CLIENT_ID` | Optional | App-Registration-Client-ID für künftige OAuth-Integration. |
| `AZURE_API_SCOPE` | Optional | API-Scope für Bearer-Token-Anforderung. |

---

## Docker

```bash
# Image bauen
docker build -f streamlit_app/Dockerfile -t bod-streamlit:latest .

# Lokal starten (Mock-Modus)
docker run -p 8501:8501 bod-streamlit:latest

# Lokal starten (Backend-Modus)
docker run -p 8501:8501 \
  -e BOARD_API_BASE_URL=http://host.docker.internal:8000 \
  bod-streamlit:latest
```

---

## Azure Container Apps Deployment

### IaC

Die Streamlit Container App ist in `infra/main.bicep` als Modul `streamlitApp` definiert.

- Image: `<acr>.azurecr.io/bod-streamlit:latest`
- Port: `8501` (externes Ingress)
- CPU: `0.25`, Memory: `0.5Gi`
- `BOARD_API_BASE_URL` wird automatisch auf den FQDN der API Container App gesetzt.

### Deployment-Schritte

1. Streamlit-Image bauen und in ACR pushen:

   ```bash
   az acr build \
     --registry <acr-name> \
     --image bod-streamlit:latest \
     --file streamlit_app/Dockerfile \
     .
   ```

2. Bicep deployen:

   ```bash
   az deployment group create \
     --resource-group <rg-name> \
     --template-file infra/main.bicep \
     --parameters \
       namePrefix=<prefix> \
       environment=prod \
       azureTenantId=<tenant-id> \
       azureApiAudience=<audience> \
       azureAiFoundryEndpoint=<endpoint> \
       azureOpenAiEndpoint=<endpoint>
   ```

3. Die Outputs `streamlitAppFqdn` und `streamlitAppName` geben die URL der fertigen App.

### Erforderliche Secrets

Die Streamlit-App benötigt im Standardbetrieb **keine Secrets** – sie kommuniziert ausschließlich mit dem FastAPI-Backend via `BOARD_API_BASE_URL`. Auth-Token werden vom Nutzer übergeben und in der Session gespeichert.

Für künftige Entra-OAuth-Integration können `AZURE_TENANT_ID`, `AZURE_CLIENT_ID` und `AZURE_API_SCOPE` als Container App Secrets oder Key Vault References konfiguriert werden.

---

## Bekannte Einschränkungen

- **Kein persistentes Session-State**: Streamlit-Session-State ist pro Browser-Tab. Bei App-Neustart oder Container-Neuzuweisung gehen laufende Wizard-Daten verloren.
- **Run-Historie**: Nur Runs der aktuellen Sitzung werden angezeigt. Ein persistenter Verlauf erfordert einen Backend-Endpunkt für Run-Listen (noch nicht implementiert).
- **Auth MVP**: Entra-Login ist noch nicht im Streamlit-Frontend implementiert. Bearer-Token müssen manuell in `st.session_state["entra_access_token"]` gesetzt werden.
- **SSE-Streaming**: Das Backend liefert SSE-Events. Im Mock-Modus werden sie deterministisch simuliert.
- **Keine Admin-Seite**: Die optionale `06_Admin.py` Seite ist im MVP nicht implementiert.
