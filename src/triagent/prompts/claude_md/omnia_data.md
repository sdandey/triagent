# Omnia Data Team Instructions

## Project Context
You are assisting the Omnia Data team with Azure DevOps operations in the Audit Cortex 2 project.

## Key Repositories
- analytic-notebooks - Databricks notebooks for data analytics
- cortexpy - Python library for Cortex operations
- data-kitchen-service - .NET data processing service
- spark-job-management - Databricks job orchestration
- cortex-datamanagement-services - Data preparation and lineage

## Databricks Environment
- Workspace: Databricks Unity Catalog
- Clusters: Use Serverless compute when available
- Storage: Unity Catalog Volumes for package deployment

## Coding Standards
- Python: Use type hints, follow PEP 8, use black for formatting
- PySpark: Follow Spark best practices for performance
- .NET: Follow C# coding conventions

## Communication
- Be concise and professional
- For code reviews, provide specific line-by-line feedback
- Include relevant ADO work item links when appropriate

---

## Telemetry Configuration

All Application Insights are backed by Log Analytics workspaces with LogAnalytics ingestion mode.

### AME (Americas) Environments

| Env | App Insights | Resource Group | Log Analytics Workspace | LAW Resource Group | Subscription |
|-----|--------------|----------------|------------------------|-------------------|--------------|
| DEV | APPIN_CORTEX_APPLICATION_GENERAL_DEV | App-Cortex-AME-DEV-RG | npdamecortexlaw | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD |
| DEV1 | APPIN_CORTEX_APPLICATION_GENERAL_DEV1 | App-Cortex-AME-DEV1-RG | npdamecortexlaw | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD |
| DEV2 | APPIN_CORTEX_APPLICATION_GENERAL_DEV2 | App-Cortex-PaaS-AME-DEV2-RG | npdamecortexlaw | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD |
| QAS | APPIN_CORTEX_APPLICATION_GENERAL_QAS | App-Cortex-AME-QAS-RG | npdamecortexlaw | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD |
| QAS1 | APPIN_CORTEX_APPLICATION_GENERAL_QAS1 | App-Cortex-AME-QAS1-RG | npdamecortexlaw | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD |
| QAS2 | APPIN_CORTEX_APPLICATION_GENERAL_QAS2 | App-Cortex-PaaS-AME-QAS2-RG | npdamecortexlaw | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD |
| LOD | APPIN_CORTEX_APPLICATION_GENERAL_LOD | App-Cortex-AME-LOD-RG | npdamecortexlaw | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD |
| STG | APPIN_CORTEX_APPLICATION_GENERAL_STG | App-Cortex-AME-STG-RG | prdamecortexlaw | app-cortex-ame-prd-shared-rg | US_AUDIT_PROD |
| STG2 | APPIN_CORTEX_APPLICATION_GENERAL_STG2 | App-Cortex-PaaS-AME-STG2-RG | prdamecortexlaw | app-cortex-ame-prd-shared-rg | US_AUDIT_PROD |
| CNT1 | APPIN_CORTEX_APPLICATION_GENERAL_CNT1 | App-Cortex-AME-CNT1-RG | prdamecortexlaw | app-cortex-ame-prd-shared-rg | US_AUDIT_PROD |
| PRD | APPIN_CORTEX_APPLICATION_GENERAL_PRD | App-Cortex-AME-PRD-RG | prdamecortexlaw | app-cortex-ame-prd-shared-rg | US_AUDIT_PROD |
| BCP | APPIN_CORTEX_APPLICATION_GENERAL_BCP | App-Cortex-AME-BCP-RG | bcpamecortexlaw | App-Cortex-AME-BCP-Shared-RG | US_AUDIT_PROD |

### EMA (Europe/Middle East/Africa) Environments

| Env | App Insights | Resource Group | Log Analytics Workspace | LAW Resource Group | Subscription |
|-----|--------------|----------------|------------------------|-------------------|--------------|
| INT | APPIN_CORTEX_APPLICATION_GENERAL_INT | App-Cortex-PaaS-EMA-INT-RG | npdemacortexlaw | app-cortex-ema-npd-shared-rg | US_AUDIT_PREPROD |
| STG | APPIN_CORTEX_APPLICATION_GENERAL_STG | App-Cortex-PaaS-EMA-STG-RG | npdemacortexlaw | app-cortex-ema-npd-shared-rg | US_AUDIT_PREPROD |
| PRD | APPIN_CORTEX_APPLICATION_GENERAL_PRD | App-Cortex-PaaS-EMA-PRD-RG | prdemacortexlaw | app-cortex-ema-prd-shared-rg | US_AUDIT_PROD |
| BCP | APPIN_CORTEX_APPLICATION_GENERAL_BCP | App-Cortex-PaaS-EMA-BCP-RG | bcpemacortexlaw | app-cortex-ema-bcp-shared-rg | US_AUDIT_PROD |

### APAC (Asia Pacific) Environments

| Env | App Insights | Resource Group | Log Analytics Workspace | LAW Resource Group | Subscription |
|-----|--------------|----------------|------------------------|-------------------|--------------|
| STG | APPIN_CORTEX_APPLICATION_GENERAL_STG | App-Cortex-PaaS-APA-STG-RG | prdapacortexlaw | App-Cortex-APA-PRD-Shared-RG | b2fcc9cc-5757-42d3-980c-d92d66bab682 |
| PRD | APPIN_CORTEX_APPLICATION_GENERAL_PRD | App-Cortex-PaaS-APA-PRD-RG | prdapacortexlaw | App-Cortex-APA-PRD-Shared-RG | b2fcc9cc-5757-42d3-980c-d92d66bab682 |
| BCP | APPIN_CORTEX_APPLICATION_GENERAL_BCP | App-Cortex-PaaS-APA-BCP-RG | bcpapacortexlaw | App-Cortex-APA-BCP-Shared-RG | b2fcc9cc-5757-42d3-980c-d92d66bab682 |

### Log Analytics Tables

| Table | Description |
|-------|-------------|
| AppExceptions | Exception details with stack traces |
| AppTraces | Application trace logs |
| AppRequests | HTTP request logs |
| AppDependencies | External dependency calls (SQL, HTTP, Service Bus) |
| AppEvents | Custom application events |
| AppMetrics | Application performance metrics |

---

## Service Names (CloudRoleName / AppRoleName)

### Analytics & Reporting
| CloudRoleName | Repository | Description |
|--------------|------------|-------------|
| AnalyticTemplateService | analytic-template-service | Analytics template management |
| AnalyticTemplateFunction | analytic-template-service | Analytics template functions |
| DataKitchenService | data-kitchen-service | Data processing and transformation |
| data-kitchen-function | data-kitchen-service | Data kitchen Azure Functions |
| NotificationService | notification-service | Notification delivery |
| Notification-UI-MFE | notification-service | Notification UI micro-frontend |

### Data Exchange & Integration
| CloudRoleName | Repository | Description |
|--------------|------------|-------------|
| DataExchangeService | data-exchange-service | Data exchange API |
| DataExchangeGateway | omniadata-dataexchange-services | Data exchange gateway |
| DataExchangeGatewayFunction | omniadata-dataexchange-services | Gateway Azure Functions |
| ExternalIntegrationService | external-integration-service | External system integration |
| ExternalIntegrationFunction | external-integration-service | Integration Azure Functions |
| IntegrationService | integration-service | Internal integration |
| InformaticaService | informatica-service | Informatica ETL integration |

### Data Management & Preparation
| CloudRoleName | Repository | Description |
|--------------|------------|-------------|
| DataPreparationService | cortex-datamanagement-services | Data preparation API |
| DataPreparationFunction | cortex-datamanagement-services | Data prep Azure Functions |
| DataPreparationGatewayService | cortex-datamanagement-services | Data prep gateway |
| EncryptionService | cortex-datamanagement-services | Encryption service |
| DataLineageService | cortex-datamanagement-services | Data lineage tracking |
| DataLineageGatewayService | cortex-datamanagement-services | Lineage gateway |
| NodeService | cortex-datamanagement-services | Node processing service |
| RetentionService | cortex-datamanagement-services | Data retention management |

### Scheduling & Orchestration
| CloudRoleName | Repository | Description |
|--------------|------------|-------------|
| SchedulerService | scheduler-service | Job scheduling |
| SparkJobManagementService | spark-job-management | Databricks job orchestration |
| SparkJobManagementFunction | spark-job-management | Spark job Azure Functions |
| async-workflow-function | async-workflow-framework | Async workflow processing |
| BundleService | bundle-service | Bundle management |

### Engagement & Collaboration
| CloudRoleName | Repository | Description |
|--------------|------------|-------------|
| EngagementService | engagement-service | Engagement management |
| EngagementServiceFunction | engagement-service | Engagement Azure Functions |
| WorkpaperService | workpaper-service | Workpaper management |
| WorkpaperFunction | workpaper-service | Workpaper Azure Functions |

### Staging & Data Ingestion
| CloudRoleName | Repository | Description |
|--------------|------------|-------------|
| StagingService | staging-service | Data staging API |
| staging-stagingservice-function | staging-service | Staging Azure Functions |
| staging-unzipfilesasyncfunction-function | staging-service | File unzip function |
| staging-datalakefileuploadlistener-function | staging-service | File upload listener |

### Core Services
| CloudRoleName | Repository | Description |
|--------------|------------|-------------|
| SecurityService | security-service | Authentication & authorization |
| KeyManagementService | key-management-service | Key/secret management |
| ClientService | client-service | Client management |
| DatalakeService | datalake-service | Data lake operations |
| DataRequestService | datarequest-service | Data request handling |
| SamplingService | sampling-service | Data sampling |
| LocalizationService | localization-service | Internationalization |
| AppSupportService | cass-service | App support (CASS) |
| Cortex-UI | cortex-ui | Main Cortex UI |

---

## Common Error Patterns

| Pattern | Investigation |
|---------|---------------|
| NullReferenceException | Check null handling in .NET services |
| TimeoutException | Check dependency latency, Databricks cluster startup time |
| SqlException | Check database connectivity, connection pool exhaustion |
| AuthenticationException | Check AAD tokens, service principal credentials |
| DatabricksException | Check Databricks workspace connectivity, cluster state |
| ServiceBusException | Check Service Bus connectivity, queue/topic configuration |

---

## Kusto Query Templates

### Exception Search
```kusto
AppExceptions
| where TimeGenerated between (datetime({start_time}) .. datetime({end_time}))
| where AppRoleName == "{service_name}"
| where ProblemId contains "{error_pattern}" or OuterMessage contains "{error_pattern}"
| summarize Count=count() by ProblemId, OuterMessage, AppRoleName
| top 20 by Count
```

### Request Failures
```kusto
AppRequests
| where TimeGenerated between (datetime({start_time}) .. datetime({end_time}))
| where AppRoleName == "{service_name}"
| where Success == false
| summarize Count=count() by Name, ResultCode, AppRoleName
| top 20 by Count
```

### Dependency Failures
```kusto
AppDependencies
| where TimeGenerated between (datetime({start_time}) .. datetime({end_time}))
| where AppRoleName == "{service_name}"
| where Success == false
| summarize Count=count() by Name, Target, ResultCode, DependencyType
| top 20 by Count
```

### Trace Logs Search
```kusto
AppTraces
| where TimeGenerated between (datetime({start_time}) .. datetime({end_time}))
| where AppRoleName == "{service_name}"
| where Message contains "{search_term}"
| project TimeGenerated, Message, SeverityLevel, AppRoleName
| top 100 by TimeGenerated desc
```
