@description('Naming prefix for resources')
param namingPrefix string

@description('Azure region for resources')
param location string

@description('Log Analytics Workspace ID for Application Insights')
param logAnalyticsWorkspaceId string

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${namingPrefix}-appinsights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Flow_Type: 'Bluefield'
    Request_Source: 'rest'
    WorkspaceResourceId: logAnalyticsWorkspaceId
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
  tags: {
    Project: 'Triagent'
    Component: 'ApplicationInsights'
  }
}

@description('Application Insights Instrumentation Key')
output instrumentationKey string = appInsights.properties.InstrumentationKey

@description('Application Insights Connection String')
output connectionString string = appInsights.properties.ConnectionString

@description('Application Insights resource ID')
output appInsightsId string = appInsights.id
