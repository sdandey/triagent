@description('Naming prefix for resources')
param namingPrefix string

@description('Azure region for resources')
param location string

// ACR names must be alphanumeric only
var acrName = replace('${namingPrefix}acr', '-', '')

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    adminUserEnabled: false
    networkRuleBypassOptions: 'AzureServices'
  }
  tags: {
    Project: 'Triagent'
    Component: 'ContainerRegistry'
  }
}

@description('ACR login server URL')
output loginServer string = acr.properties.loginServer

@description('ACR resource name')
output acrName string = acr.name

@description('ACR resource ID')
output acrId string = acr.id
