targetScope = 'subscription'

// =============================================================================
// GENERAL PARAMETERS
// =============================================================================

@description('Environment name prefix for all resources')
param namingPrefix string = 'triagent-sandbox'

@description('Azure region for resources')
param location string = 'eastus'

// =============================================================================
// APP SERVICE PARAMETERS
// =============================================================================

@description('App Service Plan SKU')
param appServiceSku string = 'S1'

// =============================================================================
// REDIS PARAMETERS
// =============================================================================

@description('Redis SKU name (Basic, Standard, Premium)')
param redisSku string = 'Standard'

// =============================================================================
// SESSION POOL PARAMETERS
// =============================================================================

@description('Maximum concurrent sessions in the pool')
param maxSessions int = 100

@description('Number of ready session instances')
param readyInstances int = 5

@description('Session cooldown period in seconds')
param cooldownSeconds int = 1800

@description('Container image tag')
param imageTag string = 'latest'

// =============================================================================
// CONTAINER REGISTRY PARAMETERS
// =============================================================================

@description('Container registry type: placeholder (default), acr, or ghcr')
@allowed(['placeholder', 'acr', 'ghcr'])
param registryType string = 'placeholder'

@description('GitHub Container Registry image path (e.g., ghcr.io/owner/triagent-session)')
param ghcrImage string = ''

@description('GitHub username for GHCR private images')
param ghcrUsername string = ''

@description('GitHub PAT token for GHCR private images (with read:packages scope)')
@secure()
param ghcrToken string = ''

// =============================================================================
// AUTHENTICATION PARAMETERS (MVP - Simple API Key)
// =============================================================================

@description('API key for simple authentication (MVP). Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"')
@secure()
param triagentApiKey string = ''

// =============================================================================
// RESOURCE GROUP
// =============================================================================

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: '${namingPrefix}-rg'
  location: location
  tags: {
    Project: 'Triagent'
    Environment: 'Sandbox'
    ManagedBy: 'Bicep'
  }
}

// =============================================================================
// MANAGED IDENTITY (for ACR access)
// =============================================================================

module managedIdentity 'modules/managedIdentity.bicep' = {
  scope: rg
  name: 'identity-deployment'
  params: {
    namingPrefix: namingPrefix
    location: location
  }
}

// =============================================================================
// AZURE CONTAINER REGISTRY
// =============================================================================

module acr 'modules/acr.bicep' = {
  scope: rg
  name: 'acr-deployment'
  params: {
    namingPrefix: namingPrefix
    location: location
  }
}

// RBAC: Grant Managed Identity ACR Pull permission (only when using ACR)
module acrPullRoleAssignment 'modules/roleAssignment.bicep' = if (registryType == 'acr') {
  scope: rg
  name: 'acr-pull-role-assignment'
  params: {
    principalId: managedIdentity.outputs.principalId
    roleDefinitionId: '7f951dda-4ed3-4680-a7ca-43fe172d538d' // AcrPull
    acrName: acr.outputs.acrName
  }
}

// =============================================================================
// LOG ANALYTICS & APPLICATION INSIGHTS
// =============================================================================

module logAnalytics 'modules/logAnalytics.bicep' = {
  scope: rg
  name: 'loganalytics-deployment'
  params: {
    namingPrefix: namingPrefix
    location: location
  }
}

module appInsights 'modules/appInsights.bicep' = {
  scope: rg
  name: 'appinsights-deployment'
  params: {
    namingPrefix: namingPrefix
    location: location
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceId
  }
}

// =============================================================================
// CONTAINER APPS ENVIRONMENT & SESSION POOL
// =============================================================================

module containerAppsEnv 'modules/containerAppsEnv.bicep' = {
  scope: rg
  name: 'cae-deployment'
  params: {
    namingPrefix: namingPrefix
    location: location
    logAnalyticsCustomerId: logAnalytics.outputs.customerId
    logAnalyticsPrimaryKey: logAnalytics.outputs.primarySharedKey
  }
}

module sessionPool 'modules/sessionPool.bicep' = {
  scope: rg
  name: 'sessionpool-deployment'
  params: {
    namingPrefix: namingPrefix
    location: location
    environmentId: containerAppsEnv.outputs.environmentId
    managedIdentityId: managedIdentity.outputs.identityId
    maxSessions: maxSessions
    readyInstances: readyInstances
    cooldownSeconds: cooldownSeconds
    imageTag: imageTag
    registryType: registryType
    acrLoginServer: acr.outputs.loginServer
    ghcrImage: ghcrImage
    ghcrUsername: ghcrUsername
    ghcrToken: ghcrToken
  }
}

// =============================================================================
// REDIS CACHE
// =============================================================================

module redis 'modules/redis.bicep' = {
  scope: rg
  name: 'redis-deployment'
  params: {
    namingPrefix: namingPrefix
    location: location
    skuName: redisSku
  }
}

// =============================================================================
// APP SERVICE (FastAPI Backend)
// =============================================================================

module appService 'modules/appService.bicep' = {
  scope: rg
  name: 'appservice-deployment'
  params: {
    namingPrefix: namingPrefix
    location: location
    sku: appServiceSku
    redisHostname: redis.outputs.hostname
    redisKey: redis.outputs.primaryKey
    sessionPoolEndpoint: sessionPool.outputs.poolEndpoint
    appInsightsConnectionString: appInsights.outputs.connectionString
    triagentApiKey: triagentApiKey
  }
}

// =============================================================================
// ROLE ASSIGNMENT: App Service -> Session Pool (Session Executor)
// NOTE: Requires Owner/User Access Admin. If deployment fails, assign manually:
//   az role assignment create --assignee <appServicePrincipalId> \
//     --role "Azure ContainerApps Session Executor" \
//     --scope <sessionPoolResourceId>
// =============================================================================

@description('Enable Session Pool role assignment (requires Owner permissions)')
param enableSessionPoolRole bool = false

module sessionPoolRole 'modules/sessionPoolRoleAssignment.bicep' = if (enableSessionPoolRole) {
  scope: rg
  name: 'sessionpool-role-assignment'
  params: {
    principalId: appService.outputs.principalId
    sessionPoolName: sessionPool.outputs.poolName
  }
}

// =============================================================================
// OUTPUTS
// =============================================================================

output resourceGroupName string = rg.name
output acrLoginServer string = acr.outputs.loginServer
output appServiceUrl string = appService.outputs.url
output sessionPoolEndpoint string = sessionPool.outputs.poolEndpoint
output redisHostname string = redis.outputs.hostname
output managedIdentityId string = managedIdentity.outputs.identityId
output appInsightsConnectionString string = appInsights.outputs.connectionString
output containerImage string = sessionPool.outputs.containerImage
