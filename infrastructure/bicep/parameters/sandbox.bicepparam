using '../main.bicep'

// Sandbox Environment Parameters
// Use with: az deployment sub create --parameters parameters/sandbox.bicepparam

param namingPrefix = 'triagent-sandbox'
param location = 'eastus'
param appServiceSku = 'S1'
param redisSku = 'Standard'
param maxSessions = 100
param readyInstances = 5
param cooldownSeconds = 1800
param imageTag = 'latest'

// Enable Session Pool role assignment (requires Owner permissions)
param enableSessionPoolRole = true
