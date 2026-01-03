---
name: telemetry_basics
display_name: "Telemetry Basics"
description: "Core telemetry concepts, Azure Log Analytics, and optimized query patterns"
version: "1.1.0"
tags: [telemetry, kusto, log-analytics, core]
requires: []
subagents: []
tools:
  - mcp__triagent__generate_kusto_query
  - mcp__triagent__list_telemetry_tables
  - Bash
triggers: []
---

## Telemetry Fundamentals

You have access to telemetry tools for querying Azure Log Analytics via MCP tools and Azure CLI.

---

## Log Analytics Workspace Reference

### AME (Americas)

| Environment | Workspace Name | Workspace ID | Subscription |
|-------------|----------------|--------------|--------------|
| DEV, DEV1, DEV2, QAS, QAS1, QAS2, LOD | npdamecortexlaw | `874aa8fb-6d29-4521-920f-63ac7168404e` | US_AUDIT_PREPROD |
| STG, STG2, CNT1, PRD | prdamecortexlaw | `ed9e6912-0544-405b-921b-f2d6aad2155e` | US_AUDIT_PROD |
| BCP | bcpamecortexlaw | `ef540bd5-ce75-4aac-8d29-7aa576b9d537` | US_AUDIT_PROD |

### EMA (Europe/Middle East/Africa)

| Environment | Workspace Name | Workspace ID | Subscription |
|-------------|----------------|--------------|--------------|
| INT | icortexjeemala | `8c9be877-4f75-45ed-b34a-e067a87918c0` | US-AZSUB-EMA-AUD-NPD-01 |
| STG | scortexjeemala | `9cb4fe2f-645d-45ae-83c0-fe5b88309aef` | US-AZSUB-EMA-AUD-PRD-01 |
| PRD | prdemacortexlaw | `b3f751c4-5cce-4caa-a3fb-eccbe019c661` | US-AZSUB-EMA-AUD-PRD-01 |

### APA (Asia Pacific)

| Environment | Workspace Name | Workspace ID | Subscription |
|-------------|----------------|--------------|--------------|
| STG, PRD | prdapacortexlaw | `d333bffc-5984-4bcd-a600-064988e7e2ec` | US_AUDIT_APA |

---

## Subscription Switching

**IMPORTANT**: Switch to the correct subscription before querying logs.

```bash
# AME Non-Prod (DEV, QAS)
az account set -s d7ac9c0b-155b-42a8-9d7d-87e883f82d5d

# AME Prod (STG, PRD)
az account set -s 8c71ef53-4473-4862-af36-bae6e40451b2

# EMA Prod
az account set -s 62c1dd5c-d918-4a4d-b0ee-18d5e7d5071b

# APA
az account set -s b2fcc9cc-5757-42d3-980c-d92d66bab682

# Verify current subscription
az account show --query "{Name:name, ID:id}" -o table
```

---

## Azure CLI Log Analytics Commands

### Basic Query Syntax

```bash
az monitor log-analytics query \
  --workspace {WORKSPACE_ID} \
  --analytics-query "{KUSTO_QUERY}" \
  -o json
```

### Optimized Query Examples

#### Exception Summary (Last 30 Days)

```bash
az monitor log-analytics query \
  --workspace ed9e6912-0544-405b-921b-f2d6aad2155e \
  --analytics-query "
    AppExceptions
    | where TimeGenerated > ago(30d)
    | where AppRoleName in ('WorkpaperService', 'WorkpaperFunction')
    | summarize Count=count(), FirstSeen=min(TimeGenerated), LastSeen=max(TimeGenerated) by ProblemId
    | order by Count desc
    | take 20
  " -o json
```

#### Detailed Exception Stack Traces

```bash
az monitor log-analytics query \
  --workspace ed9e6912-0544-405b-921b-f2d6aad2155e \
  --analytics-query "
    AppExceptions
    | where TimeGenerated > ago(7d)
    | where AppRoleName == 'WorkpaperService'
    | where ProblemId contains 'OutOfMemoryException'
    | project TimeGenerated, AppRoleName, ProblemId, OuterMessage, InnermostMessage
    | take 5
  " -o json
```

#### Daily Exception Trend

```bash
az monitor log-analytics query \
  --workspace ed9e6912-0544-405b-921b-f2d6aad2155e \
  --analytics-query "
    AppExceptions
    | where TimeGenerated > ago(30d)
    | where AppRoleName == 'WorkpaperService'
    | summarize Count=count() by bin(TimeGenerated, 1d)
    | order by TimeGenerated desc
  " -o json
```

#### Cross-Region Query Pattern

```bash
# Query all three regions in parallel
for region in "ed9e6912-0544-405b-921b-f2d6aad2155e" "b3f751c4-5cce-4caa-a3fb-eccbe019c661" "d333bffc-5984-4bcd-a600-064988e7e2ec"; do
  az monitor log-analytics query --workspace $region --analytics-query "..." &
done
wait
```

---

## Available Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `AppExceptions` | Application exceptions | ProblemId, OuterMessage, InnermostMessage, AppRoleName |
| `AppTraces` | Log traces | Message, SeverityLevel, AppRoleName |
| `AppRequests` | HTTP requests | Name, Url, ResultCode, DurationMs, Success |
| `AppDependencies` | External calls | Name, Target, DependencyType, DurationMs, Success |
| `AppMetrics` | Performance metrics | Name, Sum, Count, Min, Max |

---

## Service AppRoleName Reference

Use these CloudRoleName/AppRoleName values when filtering telemetry queries.

### Analytics & Reporting

| CloudRoleName | Repository | Description |
|---------------|------------|-------------|
| AnalyticTemplateService | analytic-template-service | Analytics template management |
| AnalyticTemplateFunction | analytic-template-service | Analytics template functions |
| DataKitchenService | data-kitchen-service | Data processing and transformation |
| data-kitchen-function | data-kitchen-service | Data kitchen Azure Functions |
| NotificationService | notification-service | Notification delivery |
| Notification-UI-MFE | notification-service | Notification UI micro-frontend |

### Data Exchange & Integration

| CloudRoleName | Repository | Description |
|---------------|------------|-------------|
| DataExchangeService | data-exchange-service | Data exchange API |
| DataExchangeGateway | omniadata-dataexchange-services | Data exchange gateway |
| DataExchangeGatewayFunction | omniadata-dataexchange-services | Gateway Azure Functions |
| ExternalIntegrationService | external-integration-service | External system integration |
| IntegrationService | integration-service | Internal integration |

### Data Management & Preparation

| CloudRoleName | Repository | Description |
|---------------|------------|-------------|
| DataPreparationService | cortex-datamanagement-services | Data preparation API |
| DataPreparationFunction | cortex-datamanagement-services | Data prep Azure Functions |
| DataPreparationGatewayService | cortex-datamanagement-services | Data prep gateway |
| EncryptionService | cortex-datamanagement-services | Encryption service |
| DataLineageService | cortex-datamanagement-services | Data lineage tracking |
| NodeService | cortex-datamanagement-services | Node processing service |
| RetentionService | cortex-datamanagement-services | Data retention management |

### Scheduling & Orchestration

| CloudRoleName | Repository | Description |
|---------------|------------|-------------|
| SchedulerService | scheduler-service | Job scheduling |
| SparkJobManagementService | spark-job-management | Databricks job orchestration |
| SparkJobManagementFunction | spark-job-management | Spark job Azure Functions |
| async-workflow-function | async-workflow-framework | Async workflow processing |
| BundleService | bundle-service | Bundle management |

### Engagement & Workpapers

| CloudRoleName | Repository | Description |
|---------------|------------|-------------|
| EngagementService | engagement-service | Engagement management |
| EngagementServiceFunction | engagement-service | Engagement Azure Functions |
| WorkpaperService | workpaper-service | Workpaper management |
| WorkpaperFunction | workpaper-service | Workpaper Azure Functions |

### Staging & Data Ingestion

| CloudRoleName | Repository | Description |
|---------------|------------|-------------|
| StagingService | staging-service | Data staging API |
| staging-stagingservice-function | staging-service | Staging Azure Functions |
| staging-unzipfilesasyncfunction-function | staging-service | File unzip function |
| staging-datalakefileuploadlistener-function | staging-service | File upload listener |

### Core Services

| CloudRoleName | Repository | Description |
|---------------|------------|-------------|
| SecurityService | security-service | Authentication & authorization |
| ClientService | client-service | Client management |
| SamplingService | sampling-service | Data sampling |
| LocalizationService | localization-service | Internationalization |
| AppSupportService | cass-service | App support (CASS) |
| Cortex-UI | cortex-ui | Main Cortex UI |

---

## Optimized Query Patterns

### 1. Filter Early, Project Late

```kusto
// Good - filter first
AppExceptions
| where TimeGenerated > ago(1d)
| where AppRoleName == "ServiceName"
| project TimeGenerated, ProblemId, OuterMessage

// Bad - project first
AppExceptions
| project TimeGenerated, ProblemId, OuterMessage, AppRoleName
| where TimeGenerated > ago(1d)
| where AppRoleName == "ServiceName"
```

### 2. Use Summarize for Large Datasets

```kusto
// Count exceptions by type
AppExceptions
| where TimeGenerated > ago(30d)
| summarize Count=count() by ProblemId
| order by Count desc
| take 20
```

### 3. Limit Results with Take

```kusto
// Always limit when exploring
AppExceptions
| where TimeGenerated > ago(1h)
| take 100
```

### 4. Use has/contains for String Matching

```kusto
// Faster: has (word boundary match)
| where ProblemId has "OutOfMemory"

// Slower: contains (substring match)
| where ProblemId contains "OutOfMemory"
```

### 5. Time-Box Large Queries

```kusto
// Start with 1 hour, expand if needed
| where TimeGenerated > ago(1h)
// Then expand: ago(1d), ago(7d), ago(30d)
```

---

## Best Practices

1. **Always filter by time first** - Limits data scanned
2. **Use Workspace ID, not name** - Required for az CLI
3. **Switch subscription before querying** - Different regions use different subscriptions
4. **Use `take` when exploring** - Prevents timeout on large datasets
5. **Parallelize cross-region queries** - Query AME, EMA, APA simultaneously
6. **Use `has` over `contains`** - 10x faster for word matching
7. **Project only needed columns** - Reduces data transfer
