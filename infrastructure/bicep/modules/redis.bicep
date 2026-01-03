@description('Naming prefix for resources')
param namingPrefix string

@description('Azure region for resources')
param location string

@description('Redis SKU name (Basic, Standard, Premium)')
param skuName string = 'Standard'

@description('Redis SKU capacity (0-6 for Basic/Standard, 1-5 for Premium)')
param capacity int = 1

resource redis 'Microsoft.Cache/redis@2024-03-01' = {
  name: '${namingPrefix}-redis'
  location: location
  properties: {
    sku: {
      name: skuName
      family: skuName == 'Premium' ? 'P' : 'C'
      capacity: capacity
    }
    redisVersion: '6'
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    redisConfiguration: {
      'maxmemory-policy': 'volatile-lru'
    }
    publicNetworkAccess: 'Enabled'
  }
  tags: {
    Project: 'Triagent'
    Component: 'Redis'
  }
}

@description('Redis hostname')
output hostname string = redis.properties.hostName

@description('Redis SSL port')
output sslPort int = redis.properties.sslPort

@description('Redis primary access key')
output primaryKey string = redis.listKeys().primaryKey

@description('Redis resource ID')
output redisId string = redis.id
