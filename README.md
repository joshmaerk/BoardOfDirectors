# Board of Directors API

Backend service for the "Board of Directors" feature of the Streamlit app
(Entra-authenticated). Users compose a board of LLM "directors" (each with role
and system prompt) and run it on a question. Modes: `parallel`, `sequential`,
`discussion`. An optional synthesis director chairs the final answer.

## Stack

- Python 3.12, FastAPI, Pydantic v2
- SQLAlchemy 2 (async) + asyncpg + Alembic
- Azure OpenAI via the `openai` SDK (Azure mode)
- Entra (Azure AD) JWT validation via JWKS

## Local development

```bash
cp .env.example .env
# For local-only iteration without a real Entra tenant:
#   set AUTH_DEV_BYPASS=true
docker compose up --build
# API on http://localhost:8000  ·  OpenAPI at /docs
```

Run migrations manually (against a running DB):

```bash
alembic upgrade head
```

## API surface (v1)

All endpoints under `/api/v1`, all protected by `Authorization: Bearer <entra-token>`
except `/healthz`.

- `GET /healthz`
- `GET /me`
- `GET/POST /directors`  ·  `GET/PUT/DELETE /directors/{id}`
- `GET/POST /boards`  ·  `GET/PUT/DELETE /boards/{id}`
- `POST /boards/{id}/runs` — start a run (returns immediately, run executes in background)
- `GET /runs/{id}` — status + all messages
- `GET /runs/{id}/messages`
- `POST /runs/{id}/cancel`
- `GET /runs/{id}/stream` — Server-Sent Events with live director messages

OpenAPI schema at `/openapi.json`.

## Streamlit integration

The Streamlit app forwards the user's Entra access token in the
`Authorization` header. The API validates it against Entra JWKS, extracts
`oid` (stable user id) and uses it for ownership/authorization.

## Configuration

See `.env.example`. The most important variables:

- `AZURE_TENANT_ID`, `AZURE_API_AUDIENCE` — Entra validation
- `AZURE_OPENAI_*` — endpoint, key, deployments (logical name → deployment name)
- `DATABASE_URL` — async Postgres URL (`postgresql+asyncpg://...`)
- `ALLOWED_ORIGINS` — comma-separated list (the Streamlit origin)
- `AUTH_DEV_BYPASS` — local-only, accepts any request as a fake user
