@description('Naming prefix for resources')
param namingPrefix string

@description('Azure region for resources')
param location string

@description('Log Analytics Workspace Customer ID')
param logAnalyticsCustomerId string

@description('Log Analytics Workspace Primary Key')
@secure()
param logAnalyticsPrimaryKey string

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${namingPrefix}-cae'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsPrimaryKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
  tags: {
    Project: 'Triagent'
    Component: 'ContainerAppsEnvironment'
  }
}

@description('Container Apps Environment ID')
output environmentId string = containerAppsEnv.id

@description('Container Apps Environment Default Domain')
output defaultDomain string = containerAppsEnv.properties.defaultDomain
