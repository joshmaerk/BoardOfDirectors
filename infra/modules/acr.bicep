// Container Registry that holds api + worker images.

param namePrefix string
param environment string
param location string
param tags object

resource registry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  // ACR names must be globally unique and alphanumeric.
  name: toLower(replace('${namePrefix}acr${environment}', '-', ''))
  location: location
  tags: tags
  sku: { name: 'Standard' }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

output name string = registry.name
output loginServer string = registry.properties.loginServer
output id string = registry.id
