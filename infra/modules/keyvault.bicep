// Key Vault with RBAC, plus a role assignment for the on-call admin group.

param namePrefix string
param environment string
param location string
param tags object
param tenantId string
param adminObjectId string

resource kv 'Microsoft.KeyVault/vaults@2024-04-01-preview' = {
  name: '${namePrefix}-kv-${environment}'
  location: location
  tags: tags
  properties: {
    tenantId: tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    publicNetworkAccess: 'Enabled' // tightened by private endpoint in a follow-up
  }
}

// Key Vault Secrets User role (used by Container Apps' Managed Identity at
// runtime to resolve `@kv:<name>` references).
var kvSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource adminRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(adminObjectId)) {
  name: guid(kv.id, adminObjectId, kvSecretsUserRoleId)
  scope: kv
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', kvSecretsUserRoleId)
    principalId: adminObjectId
    principalType: 'Group'
  }
}

output name string = kv.name
output uri string = kv.properties.vaultUri
output id string = kv.id
