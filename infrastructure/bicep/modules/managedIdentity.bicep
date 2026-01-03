@description('Naming prefix for resources')
param namingPrefix string

@description('Azure region for resources')
param location string

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${namingPrefix}-session-identity'
  location: location
  tags: {
    Project: 'Triagent'
    Component: 'ManagedIdentity'
  }
}

@description('Managed identity resource ID')
output identityId string = managedIdentity.id

@description('Managed identity principal ID')
output principalId string = managedIdentity.properties.principalId

@description('Managed identity client ID')
output clientId string = managedIdentity.properties.clientId
