# Architecture

## Context

The Board of Directors backend serves the Streamlit app's "Board of Directors"
feature. Users build a board out of LLM "directors" (persona + role + model)
and run it on a question. The API multiplexes across multiple LLM providers
and orchestrates parallel/sequential/discussion modes server-side, persisting
each director's contribution and streaming intermediate results to the UI.

## High-level boxes

```
   ┌────────────────────────┐                ┌──────────────────────────┐
   │  Streamlit (legacy)    │  Bearer JWT    │  Board of Directors API  │
   │  • Entra OIDC login    │ ─────────────▶ │  (FastAPI, Azure         │
   │  • UI for directors,   │                │   Container Apps)        │
   │    boards, run history │ ◀───────────── │                          │
   └────────────────────────┘   JSON + SSE   └──────┬───────────────────┘
                                                    │
                                  enqueue           │
                          ┌─────────────────────────┴────────────────┐
                          │                                          │
                          ▼                                          ▼
                ┌──────────────────┐                       ┌─────────────────┐
                │ Azure Cache for  │     pop job           │  Worker         │
                │ Redis (ARQ queue)│ ◀────────────────────▶│  (Container App)│
                └──────────────────┘                       └────────┬────────┘
                          ▲                                         │
                          │                                         │ LLM calls
                          │                                         ▼
                          │                          ┌────────────────────────────┐
                          │                          │ Azure OpenAI               │
                          │                          │ Azure AI Foundry (Claude)  │
                          │                          └────────────────────────────┘
                          │                                         │
                          ▼                                         ▼
                ┌────────────────────────┐               ┌─────────────────────────┐
                │ Azure Postgres         │ ◀──── reads ──│ persist messages,       │
                │ (Flexible Server)      │               │ tokens, audit log       │
                └────────────────────────┘               └─────────────────────────┘
```

## Data flow: one run

1. Streamlit sends `POST /api/v1/boards/{id}/runs` with `{input, mode_override?}`.
2. API validates Entra JWT (tenant + audience + roles via JWKS) and the
   request size limits.
3. A `Run` row is inserted with `status=pending`, an `audit_event` row
   `run.started` written in the same transaction.
4. The API enqueues the run id to Redis via ARQ
   (`app.services.queue.arq_queue.ARQQueue`).
5. The worker pops the job, instantiates `BoardRunner`, executes the
   configured mode (parallel / sequential / discussion), persists each
   `DirectorMessage` and updates `Run.status` as it progresses.
6. Streamlit polls `GET /runs/{id}` or attaches to `GET /runs/{id}/stream`
   (Server-Sent Events) to see messages as they land.
7. If the user calls `POST /runs/{id}/cancel`, the runner sees the status
   flip on its next `_is_cancelled()` check between modes.

## Key design decisions

- **LLM provider abstraction** (`app.services.llm.LLMRouter`). A model
  name like `gpt-4o-mini` or `claude-sonnet-4-5` is routed to the right
  client via `LLM_PROVIDER_MAP`. Both providers are wrapped in
  `RetryingLLMClient` so 429 / 5xx / transport failures back off and retry.
- **Run-queue abstraction** (`app.services.queue.RunQueue`). Two backends:
  `InProcessQueue` (asyncio task; dev/single-replica) and `ARQQueue`
  (Redis; prod). Switched per environment via `RUN_QUEUE_BACKEND`.
- **Auth at the edge**. API never calls Anthropic / OpenAI directly with the
  user's identity; ownership is enforced on every resource via the `oid`
  claim. Service-to-Azure calls use the App's Managed Identity (Key Vault,
  ACR, Foundry).
- **Audit trail** in Postgres (`audit_events`). One row per mutating
  request, written in the same DB transaction as the mutation. Survives
  user delete (`DELETE /me` anonymises rather than wipes).
- **Soft-delete** on user-facing resources. Hard-delete is reserved for
  DSGVO right-to-be-forgotten via `DELETE /me`.

## Azure topology

| Resource | Why |
|---|---|
| Container Apps Environment | Hosts the two apps (api, worker) on a shared Log Analytics workspace |
| Container App `api` | External ingress on 8000, liveness/readiness probes on `/healthz` and `/readyz` |
| Container App `worker` | No ingress; runs `arq app.workers.runner_worker.WorkerSettings` |
| Postgres Flexible Server | Single source of truth for boards, runs, messages, audit |
| Azure Cache for Redis | ARQ job queue + slowapi rate-limit buckets |
| Azure Key Vault | Holds `database-url`, `redis-url`, provider keys; resolved at startup by `app.core.secrets.hydrate_env_from_key_vault` |
| Application Insights / Log Analytics | structlog JSON sink → AppInsights, all `http_request` events correlated by `X-Request-ID` |
| Azure Container Registry | Holds `bod:<sha>` images; pulled by ACA via system-assigned MI (`AcrPull` role) |

## What's deliberately out of scope (v1)

- VNet integration and Private Endpoints for Postgres / Redis / KV (network
  is currently "public, but tight" — add via a follow-up Bicep module).
- Blue/green slot swap. Container Apps' single-revision mode is used; for
  zero-downtime promotions enable multi-revision mode and add traffic-split.
- Cross-region DR. Single-region today.
- Per-route rate-limits beyond the global `RATE_LIMIT_DEFAULT` (the `RUNS`
  bucket is configurable but enforcement is the next iteration).
