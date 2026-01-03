@description('Principal ID to assign the role to (App Service managed identity)')
param principalId string

@description('Session Pool resource name')
param sessionPoolName string

// Azure ContainerApps Session Executor role
// This role allows the principal to execute code in Dynamic Sessions
var sessionExecutorRoleId = '0fb8eba5-a2bb-4abe-b1c1-49dfad359bb0'

resource sessionPool 'Microsoft.App/sessionPools@2025-01-01' existing = {
  name: sessionPoolName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(sessionPool.id, principalId, sessionExecutorRoleId)
  scope: sessionPool
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', sessionExecutorRoleId)
    principalType: 'ServicePrincipal'
  }
}

output roleAssignmentId string = roleAssignment.id
