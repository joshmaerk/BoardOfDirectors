// Azure Cache for Redis (used by ARQ + slowapi rate-limit buckets).

param namePrefix string
param environment string
param location string
param tags object

resource cache 'Microsoft.Cache/redis@2024-03-01' = {
  name: '${namePrefix}-redis-${environment}'
  location: location
  tags: tags
  properties: {
    sku: { name: 'Basic', family: 'C', capacity: 0 }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

output hostname string = cache.properties.hostName
output sslPort int = cache.properties.sslPort
