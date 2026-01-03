@description('Naming prefix for resources')
param namingPrefix string

@description('Azure region for resources')
param location string

@description('Log Analytics retention in days')
param retentionInDays int = 30

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${namingPrefix}-law'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionInDays
  }
  tags: {
    Project: 'Triagent'
    Component: 'LogAnalytics'
  }
}

@description('Log Analytics Workspace ID')
output workspaceId string = logAnalyticsWorkspace.id

@description('Log Analytics Workspace Customer ID')
output customerId string = logAnalyticsWorkspace.properties.customerId

@description('Log Analytics Workspace Primary Key')
output primarySharedKey string = logAnalyticsWorkspace.listKeys().primarySharedKey
