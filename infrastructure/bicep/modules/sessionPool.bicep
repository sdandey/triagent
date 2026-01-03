@description('Naming prefix for resources')
param namingPrefix string

@description('Azure region for resources')
param location string

@description('Container Apps Environment ID')
param environmentId string

@description('User-assigned managed identity resource ID')
param managedIdentityId string

@description('Maximum concurrent sessions')
param maxSessions int = 100

@description('Number of ready session instances')
param readyInstances int = 5

@description('Session cooldown period in seconds')
param cooldownSeconds int = 1800

@description('Maximum session alive period in seconds (max 7200 = 2 hours)')
param maxAliveSeconds int = 7200

@description('Container image tag')
param imageTag string = 'latest'

@description('Container registry type: placeholder, acr, or ghcr')
@allowed(['placeholder', 'acr', 'ghcr'])
param registryType string = 'placeholder'

@description('ACR login server URL (required if registryType is acr)')
param acrLoginServer string = ''

@description('GitHub Container Registry image (e.g., ghcr.io/owner/repo)')
param ghcrImage string = ''

@description('GitHub username for GHCR (required for private images)')
param ghcrUsername string = ''

@description('GitHub PAT for GHCR (required for private images)')
@secure()
param ghcrToken string = ''

// Determine container image based on registry type
var containerImage = registryType == 'placeholder'
  ? 'mcr.microsoft.com/k8se/quickstart:latest'
  : registryType == 'acr'
    ? '${acrLoginServer}/triagent-session:${imageTag}'
    : '${ghcrImage}:${imageTag}'

// Registry credentials based on type
var useAcrCredentials = registryType == 'acr'
var useGhcrCredentials = registryType == 'ghcr' && !empty(ghcrToken)

resource sessionPool 'Microsoft.App/sessionPools@2025-01-01' = {
  name: '${namingPrefix}-session-pool'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityId}': {}
    }
  }
  properties: {
    containerType: 'CustomContainer'
    poolManagementType: 'Dynamic'
    environmentId: environmentId

    customContainerTemplate: {
      containers: [
        {
          name: 'triagent-session'
          image: containerImage
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            {
              name: 'TRIAGENT_SESSION_MODE'
              value: 'true'
            }
            {
              name: 'PORT'
              value: '8080'
            }
          ]
        }
      ]
      ingress: {
        targetPort: 8080
      }
      // ACR credentials (using managed identity)
      registryCredentials: useAcrCredentials ? {
        server: acrLoginServer
        identity: managedIdentityId
      } : useGhcrCredentials ? {
        server: 'ghcr.io'
        username: ghcrUsername
        passwordSecretRef: 'ghcr-token'
      } : null
    }

    scaleConfiguration: {
      maxConcurrentSessions: maxSessions
      readySessionInstances: readyInstances
    }

    dynamicPoolConfiguration: {
      lifecycleConfiguration: {
        lifecycleType: 'Timed'
        cooldownPeriodInSeconds: cooldownSeconds
        maxAlivePeriodInSeconds: maxAliveSeconds
      }
    }

    sessionNetworkConfiguration: {
      status: 'EgressEnabled'
    }

    managedIdentitySettings: [
      {
        identity: managedIdentityId
        lifecycle: 'Main'
      }
    ]

    // Secrets for GHCR token (only if using GHCR with auth)
    secrets: useGhcrCredentials ? [
      {
        name: 'ghcr-token'
        value: ghcrToken
      }
    ] : []
  }
  tags: {
    Project: 'Triagent'
    Component: 'SessionPool'
  }
}

@description('Session Pool resource ID')
output poolId string = sessionPool.id

@description('Session Pool resource name')
output poolName string = sessionPool.name

@description('Session Pool management endpoint')
output poolEndpoint string = sessionPool.properties.poolManagementEndpoint

@description('Container image being used')
output containerImage string = containerImage
