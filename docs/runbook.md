# Runbook

On-call playbook for the Board of Directors API in production.

## TL;DR

| Symptom | First check | Likely cause |
|---|---|---|
| `/healthz` returns 200 but `/readyz` returns 503 | Postgres / Redis reachable from the App? | DB / Redis outage, firewall change |
| 5xx surge on `POST /boards/{id}/runs` | App Insights `http_request` logs, recent deploy? | Bad image, schema migration failed |
| Runs stay `pending` forever | Is the worker app running? Is Redis healthy? | Worker container crashed, queue saturated |
| `401` for valid token | JWKS cache, `tid`/`aud` match settings? | Token from wrong tenant, audience misconfigured |
| `429` for one user | slowapi bucket | Real abuse / runaway script — confirm with `X-Request-ID` traces |

---

## 1. Setting up local credentials

```bash
az login --tenant <AZURE_TENANT_ID>
az account set --subscription <AZURE_SUBSCRIPTION_ID>
RG=rg-bod-prod
API_APP=bod-api-prod
WORKER_APP=bod-worker-prod
```

## 2. Looking at logs

```bash
# Live tail (api)
az containerapp logs show -g "$RG" -n "$API_APP" --tail 100 --follow

# Live tail (worker)
az containerapp logs show -g "$RG" -n "$WORKER_APP" --tail 100 --follow

# Correlate a request across api + worker via X-Request-ID
TRACE=37f1a4d3-...
az monitor app-insights query \
  --app bod-ai-prod \
  -g "$RG" \
  --analytics-query "traces | where customDimensions.request_id == '${TRACE}' | order by timestamp asc"
```

## 3. Restart workers

```bash
# Force a new revision (no image change, just bounce)
az containerapp revision restart \
  -g "$RG" -n "$WORKER_APP" \
  --revision "$(az containerapp show -g "$RG" -n "$WORKER_APP" --query properties.latestRevisionName -o tsv)"
```

## 4. Inspect / clean up a stuck run

```bash
# Open a psql shell from your laptop (assumes you're in the KV-admin group).
PGPASSWORD=$(az keyvault secret show --vault-name bod-kv-prod -n database-url --query value -o tsv \
            | sed -E 's#.*://[^:]+:([^@]+)@.*#\1#')
PGHOST=$(az postgres flexible-server show -g "$RG" -n bod-pg-prod --query fullyQualifiedDomainName -o tsv)

psql "host=$PGHOST user=bodadmin dbname=bod sslmode=require" -c "
  select id, status, started_at, finished_at, error
  from runs
  where status in ('pending','running')
  order by created_at desc
  limit 20;"
```

To force-cancel a stuck run:

```sql
UPDATE runs SET status='cancelled', finished_at=now() WHERE id = '<run-id>';
```

The worker's `_is_cancelled()` check will pick this up at the next phase
boundary.

## 5. Rotate a Key Vault secret without redeploy

```bash
az keyvault secret set --vault-name bod-kv-prod -n database-url \
  --value "postgresql+asyncpg://..." >/dev/null

# Restart api + worker so they pick up the new env on startup
az containerapp revision restart -g "$RG" -n "$API_APP"  --revision <latest>
az containerapp revision restart -g "$RG" -n "$WORKER_APP" --revision <latest>
```

## 6. Roll back to the previous image

```bash
# List the last few revisions
az containerapp revision list -g "$RG" -n "$API_APP" \
  --query "[].{name:name, image:properties.template.containers[0].image, active:properties.active, trafficWeight:properties.trafficWeight}" -o table

# Activate the previous one
az containerapp revision activate -g "$RG" -n "$API_APP" --revision <previous>
az containerapp revision deactivate -g "$RG" -n "$API_APP" --revision <broken>
# Repeat for the worker.
```

## 7. DSGVO Subject Access Request

```bash
# Whoever asked for an export should hit the API with their own token:
curl -H "Authorization: Bearer $TOKEN" \
     https://${API_FQDN}/api/v1/me/export > sar.json
```

For an admin-driven export (user lost access) — open a SQL shell and
collect their rows by `owner_id`. Document the request in the audit trail.

## 8. Right-to-be-forgotten

End-user route:

```bash
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
     https://${API_FQDN}/api/v1/me
```

Hard-deletes the user's directors / boards / runs / messages and
anonymises their `audit_events` rows. The deletion itself is audited
(`account.deleted`) before the wipe.

## 9. After a Postgres failover

- Run `alembic upgrade head` to be sure schema is current (no-op if already
  applied).
- Watch `/readyz` until it returns 200.
- Re-enable traffic if you took the api app out of rotation.

## 10. Common pitfalls

- **Worker silently dies after a deploy** — usually a missing env var.
  Check `azure_openai_endpoint` / `azure_ai_foundry_endpoint` resolve to
  something at worker startup (`worker_started` log entry includes settings).
- **`/me/export` slow on heavy users** — the export is a single API request
  with no pagination. If a user has thousands of runs, route them through a
  job (not yet implemented; track in backlog).
- **SSE clients hang** — the keep-alive interval is implicit via
  `sse-starlette`. If clients drop, check Container Apps idle timeout
  (default 240s) — increase via revision setting.
