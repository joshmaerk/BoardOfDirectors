// Board of Directors API — Azure infrastructure
//
// Deploy:
//   az group create -n rg-bod-prod -l westeurope
//   az deployment group create \
//     -g rg-bod-prod \
//     -f infra/main.bicep \
//     -p infra/main.parameters.json
//
// Outputs are picked up by the deploy workflow to address the freshly built
// container image at the right registry / app.

targetScope = 'resourceGroup'

@description('Short name prefix; resources are derived as <prefix>-<role>-<env>.')
@minLength(3)
@maxLength(12)
param namePrefix string = 'bod'

@description('Environment slug (prod, staging, dev). Used in resource names and tags.')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'prod'

@description('Region for all resources.')
param location string = resourceGroup().location

@description('Entra tenant id whose tokens this API accepts.')
param azureTenantId string

@description('JWT audience the API enforces (e.g. api://<app-id>).')
param azureApiAudience string

@description('Azure AI Foundry endpoint that hosts Claude deployments.')
param azureAiFoundryEndpoint string = ''

@description('Azure OpenAI endpoint for GPT models.')
param azureOpenAiEndpoint string = ''

@description('Object id of the principal allowed to read secrets from Key Vault during incident response (e.g. an Entra group of on-call engineers).')
param keyVaultAdminObjectId string = ''

@description('Postgres admin user.')
param postgresAdminLogin string = 'bodadmin'

@secure()
@description('Postgres admin password. Stored only as the FlexibleServer login; the API uses a Managed-Identity-backed connection.')
param postgresAdminPassword string

var tags = {
  workload: 'board-of-directors'
  environment: environment
}

// ---------------------------------------------------------------------------
// Core infrastructure modules
// ---------------------------------------------------------------------------

module logging 'modules/logging.bicep' = {
  name: 'logging'
  params: {
    namePrefix: namePrefix
    environment: environment
    location: location
    tags: tags
  }
}

module kv 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    namePrefix: namePrefix
    environment: environment
    location: location
    tags: tags
    tenantId: azureTenantId
    adminObjectId: keyVaultAdminObjectId
  }
}

module acr 'modules/acr.bicep' = {
  name: 'acr'
  params: {
    namePrefix: namePrefix
    environment: environment
    location: location
    tags: tags
  }
}

module postgres 'modules/postgres.bicep' = {
  name: 'postgres'
  params: {
    namePrefix: namePrefix
    environment: environment
    location: location
    tags: tags
    adminLogin: postgresAdminLogin
    adminPassword: postgresAdminPassword
  }
}

module redis 'modules/redis.bicep' = {
  name: 'redis'
  params: {
    namePrefix: namePrefix
    environment: environment
    location: location
    tags: tags
  }
}

// ---------------------------------------------------------------------------
// Container Apps environment + two apps (api, worker)
// ---------------------------------------------------------------------------

module env 'modules/aca_env.bicep' = {
  name: 'aca-env'
  params: {
    namePrefix: namePrefix
    environment: environment
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logging.outputs.workspaceId
    logAnalyticsWorkspaceSharedKey: logging.outputs.workspaceSharedKey
  }
}

module apiApp 'modules/aca_app.bicep' = {
  name: 'aca-api'
  params: {
    name: '${namePrefix}-api-${environment}'
    location: location
    tags: tags
    environmentId: env.outputs.environmentId
    acrLoginServer: acr.outputs.loginServer
    cpu: '0.5'
    memory: '1.0Gi'
    minReplicas: 1
    maxReplicas: 5
    targetPort: 8000
    ingressExternal: true
    keyVaultName: kv.outputs.name
    keyVaultUri: kv.outputs.uri
    appInsightsConnectionString: logging.outputs.appInsightsConnectionString
    envVars: [
      { name: 'RUN_QUEUE_BACKEND', value: 'arq' }
      { name: 'AZURE_TENANT_ID', value: azureTenantId }
      { name: 'AZURE_API_AUDIENCE', value: azureApiAudience }
      { name: 'AZURE_AI_FOUNDRY_ENDPOINT', value: azureAiFoundryEndpoint }
      { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAiEndpoint }
      { name: 'EXPOSE_OPENAPI_DOCS', value: 'false' }
      { name: 'AZURE_KEY_VAULT_URL', value: kv.outputs.uri }
      // Connection strings come from Key Vault references; the secret names
      // are written by the deploy workflow when secrets are seeded.
      { name: 'DATABASE_URL', secretRef: 'database-url' }
      { name: 'REDIS_URL', secretRef: 'redis-url' }
    ]
    secrets: [
      {
        name: 'database-url'
        keyVaultUrl: '${kv.outputs.uri}secrets/database-url'
        identity: 'system'
      }
      {
        name: 'redis-url'
        keyVaultUrl: '${kv.outputs.uri}secrets/redis-url'
        identity: 'system'
      }
    ]
    command: ['sh', '-c']
    args: ['alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000']
  }
}

module workerApp 'modules/aca_app.bicep' = {
  name: 'aca-worker'
  params: {
    name: '${namePrefix}-worker-${environment}'
    location: location
    tags: tags
    environmentId: env.outputs.environmentId
    acrLoginServer: acr.outputs.loginServer
    cpu: '0.5'
    memory: '1.0Gi'
    minReplicas: 1
    maxReplicas: 3
    targetPort: 0 // no ingress
    ingressExternal: false
    keyVaultName: kv.outputs.name
    keyVaultUri: kv.outputs.uri
    appInsightsConnectionString: logging.outputs.appInsightsConnectionString
    envVars: [
      { name: 'AZURE_AI_FOUNDRY_ENDPOINT', value: azureAiFoundryEndpoint }
      { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAiEndpoint }
      { name: 'AZURE_KEY_VAULT_URL', value: kv.outputs.uri }
      { name: 'DATABASE_URL', secretRef: 'database-url' }
      { name: 'REDIS_URL', secretRef: 'redis-url' }
    ]
    secrets: [
      {
        name: 'database-url'
        keyVaultUrl: '${kv.outputs.uri}secrets/database-url'
        identity: 'system'
      }
      {
        name: 'redis-url'
        keyVaultUrl: '${kv.outputs.uri}secrets/redis-url'
        identity: 'system'
      }
    ]
    command: ['arq']
    args: ['app.workers.runner_worker.WorkerSettings']
  }
}

// ---------------------------------------------------------------------------
// Outputs consumed by the deploy workflow
// ---------------------------------------------------------------------------

output acrLoginServer string = acr.outputs.loginServer
output acrName string = acr.outputs.name
output keyVaultName string = kv.outputs.name
output keyVaultUri string = kv.outputs.uri
output apiAppName string = apiApp.outputs.name
output apiAppFqdn string = apiApp.outputs.fqdn
output workerAppName string = workerApp.outputs.name
output postgresFqdn string = postgres.outputs.fqdn
output redisHostname string = redis.outputs.hostname
output appInsightsConnectionString string = logging.outputs.appInsightsConnectionString
