// Log Analytics workspace + Application Insights (workspace-based).

param namePrefix string
param environment string
param location string
param tags object

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${namePrefix}-logs-${environment}'
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${namePrefix}-ai-${environment}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace.id
  }
}

output workspaceId string = workspace.id
output workspaceSharedKey string = workspace.listKeys().primarySharedKey
output appInsightsConnectionString string = appInsights.properties.ConnectionString
