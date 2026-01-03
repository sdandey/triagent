@description('Naming prefix for resources')
param namingPrefix string

@description('Azure region for resources')
param location string

@description('App Service Plan SKU')
param sku string = 'S1'

@description('Redis hostname')
param redisHostname string

@description('Redis primary key')
@secure()
param redisKey string

@description('Session Pool management endpoint')
param sessionPoolEndpoint string

@description('Application Insights connection string')
param appInsightsConnectionString string

@description('API key for simple authentication (MVP)')
@secure()
param triagentApiKey string = ''

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${namingPrefix}-asp'
  location: location
  kind: 'linux'
  sku: {
    name: sku
  }
  properties: {
    reserved: true
  }
  tags: {
    Project: 'Triagent'
    Component: 'AppServicePlan'
  }
}

resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: '${namingPrefix}-app'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      alwaysOn: true
      healthCheckPath: '/health'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'TRIAGENT_REDIS_HOST'
          value: redisHostname
        }
        {
          name: 'TRIAGENT_REDIS_PASSWORD'
          value: redisKey
        }
        {
          name: 'TRIAGENT_REDIS_PORT'
          value: '6380'
        }
        {
          name: 'TRIAGENT_REDIS_SSL'
          value: 'true'
        }
        {
          name: 'TRIAGENT_SESSION_POOL_ENDPOINT'
          value: sessionPoolEndpoint
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        {
          name: 'ApplicationInsightsAgent_EXTENSION_VERSION'
          value: '~3'
        }
        {
          name: 'AUTH_MODE'
          value: 'api_key'
        }
        {
          name: 'TRIAGENT_API_KEY'
          value: triagentApiKey
        }
      ]
    }
  }
  tags: {
    Project: 'Triagent'
    Component: 'AppService'
  }
}

@description('App Service URL')
output url string = 'https://${webApp.properties.defaultHostName}'

@description('App Service system-assigned principal ID')
output principalId string = webApp.identity.principalId

@description('App Service resource name')
output appName string = webApp.name
