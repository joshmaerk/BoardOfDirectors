// A single Container App (used for both the api and the worker). Uses
// System-Assigned Managed Identity so Key Vault references and ACR pulls
// don't need long-lived secrets.

param name string
param location string
param tags object
param environmentId string
param acrLoginServer string
param cpu string = '0.5'
param memory string = '1.0Gi'
param minReplicas int = 1
param maxReplicas int = 5
param targetPort int = 8000
param ingressExternal bool = true
param keyVaultName string
param keyVaultUri string
param appInsightsConnectionString string

@description('Plain (non-secret) environment variables to inject.')
param envVars array = []

@description('Container App secrets, typically Key Vault references.')
param secrets array = []

@description('Container entry-point override (image default if empty).')
param command array = []

@description('Container args (image default if empty).')
param args array = []

// Image tag is set by the deploy workflow after `az acr build` finishes.
@description('Container image (registry/repository:tag).')
param image string = '${acrLoginServer}/bod:latest'

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: tags
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: targetPort > 0 ? {
        external: ingressExternal
        targetPort: targetPort
        transport: 'http'
        allowInsecure: false
      } : null
      registries: [
        {
          server: acrLoginServer
          identity: 'system'
        }
      ]
      secrets: secrets
    }
    template: {
      containers: [
        {
          name: name
          image: image
          command: empty(command) ? null : command
          args: empty(args) ? null : args
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: concat(envVars, [
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsightsConnectionString
            }
          ])
          probes: targetPort > 0 ? [
            {
              type: 'Liveness'
              httpGet: { path: '/api/v1/healthz', port: targetPort }
              initialDelaySeconds: 5
              periodSeconds: 10
            }
            {
              type: 'Readiness'
              httpGet: { path: '/api/v1/readyz', port: targetPort }
              initialDelaySeconds: 5
              periodSeconds: 10
            }
          ] : []
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
      }
    }
  }
}

// Give this App's Managed Identity the Key Vault Secrets User role so the
// `@kv:<name>` references resolve.
var kvSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource kvRef 'Microsoft.KeyVault/vaults@2024-04-01-preview' existing = {
  name: keyVaultName
}

resource kvRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(app.id, kvRef.id, kvSecretsUserRoleId)
  scope: kvRef
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', kvSecretsUserRoleId)
    principalId: app.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// AcrPull so the Managed Identity can pull images.
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource acrRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(app.id, 'acr-pull', acrPullRoleId)
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
    principalId: app.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output name string = app.name
output fqdn string = targetPort > 0 ? app.properties.configuration.ingress.fqdn : ''
output principalId string = app.identity.principalId
