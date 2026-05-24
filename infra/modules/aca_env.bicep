// Container Apps environment, log-stream sink: Log Analytics.

param namePrefix string
param environment string
param location string
param tags object
param logAnalyticsWorkspaceId string

@secure()
param logAnalyticsWorkspaceSharedKey string

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${namePrefix}-env-${environment}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(logAnalyticsWorkspaceId, '2023-09-01').customerId
        sharedKey: logAnalyticsWorkspaceSharedKey
      }
    }
    zoneRedundant: false
  }
}

output environmentId string = env.id
output environmentName string = env.name
