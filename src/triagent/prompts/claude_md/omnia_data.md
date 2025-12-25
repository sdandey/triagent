# Omnia Data Team Instructions

## Project Context
You are assisting the Omnia Data team with Azure DevOps operations in the Audit Cortex 2 project.

## Azure DevOps Repositories

### Organization Details
- **Organization**: symphonyvsts
- **Project**: Audit Cortex 2
- **Git SSH Base**: `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/`
- **Local Clone Path**: `~/code/{repo-name}`

### Active Repositories (Monitored Services)

| Repository | Branch | AppRoleName | SSH Clone URL |
|------------|--------|-------------|---------------|
| data-exchange-service | master | DataExchangeGateway | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/data-exchange-service` |
| cortex-datamanagement-services | master | AppSupportService, DataPreparationService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/cortex-datamanagement-services` |
| engagement-service | master | EngagementService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/engagement-service` |
| security-service | master | SecurityService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/security-service` |
| data-kitchen-service | master | DataKitchenService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/data-kitchen-service` |
| analytic-template-service | master | AnalyticTemplateService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/analytic-template-service` |
| notification-service | master | NotificationService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/notification-service` |
| staging-service | master | StagingService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/staging-service` |
| spark-job-management | master | SparkJobManagementService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/spark-job-management` |
| cortex-ui | master | Cortex-UI | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/cortex-ui` |
| client-service | master | ClientService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/client-service` |
| workpaper-service | master | WorkpaperService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/workpaper-service` |
| async-workflow-framework | master | async-workflow-function | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/async-workflow-framework` |
| sampling-service | master | SamplingService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/sampling-service` |
| localization-service | master | LocalizationService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/localization-service` |
| scheduler-service | master | SchedulerService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/scheduler-service` |
| cortexpy | master | cortexpy | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/cortexpy` |
| analytic-notebooks | master | analytic-notebooks | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/analytic-notebooks` |

### Repository Ownership & Contributors

This section shows the owning team and top contributors (by commit count from develop branch, last 6 months) for each repository. Use this to identify subject matter experts for investigation.

#### data-exchange-service
- **POD**: Data Acquisition and Preparation / Data In Use | **Team**: Alpha, Kilo
- **Top Contributors**: Santhosh Patnam (27), Jitendra Nadkar (14) [Alpha], Kumbhalkar Mahesh (13) [Kilo], Satish Jare (11), Shrivastava Rahul (8)

#### cortex-datamanagement-services
- **POD**: Data Management and Activation | **Team**: Gamma
- **Top Contributors**: Katz Yoni (14) [Gamma], Pratap Anuj (11) [Gamma], Vikas J (7), Kumar Shubham (7), Shaikh Faisal (6)

#### engagement-service
- **POD**: Data Acquisition and Preparation / Data Mgmt & Activation | **Team**: Alpha, Skyrockets
- **Top Contributors**: Awasthi Harshal (32) [Alpha], Dhage Priyanka (25) [Skyrockets], Nadkar Jitendra (7) [Alpha], Kolhe Rakesh (5), Jadhav Anurag (4) [Skyrockets]

#### security-service
- **POD**: Data Management and Activation | **Team**: Skyrockets
- **Top Contributors**: Jadhav Anurag (61) [Skyrockets], Awasthi Harshal (19) [Alpha], Kumar Shubham (6), Kolhe Rakesh (4), Dhage Priyanka (3) [Skyrockets]

#### data-kitchen-service
- **POD**: Data Acquisition and Preparation | **Team**: Beta, Megatron
- **Top Contributors**: Shinde Rohini (38) [Beta], Pandey Divy Mohan (20) [Megatron], Arumugasamy Ilango (11), Hassan Abul (6), Nallamotu Teja Sri (4)

#### analytic-template-service
- **POD**: Data In Use | **Team**: Tera
- **Top Contributors**: Salunke Amol Rohidas (30) [Tera], Rajpoot Mahendra Singh (29) [Tera], Bhujbal Sanket Nitin (24), Jadhav Dhanashri Niraj (9), Shelke Rahul Somnath (8)

#### notification-service
- **POD**: Data Acquisition and Preparation / Data Mgmt & Activation | **Team**: Beta, Skyrockets
- **Top Contributors**: Bagchi Indrajit (21) [Beta], Jadhav Anurag (9) [Skyrockets], Agrawal Sakshi (6) [Skyrockets], Rohan Prabhu (5), Borse Rajendra (4)

#### staging-service
- **POD**: Data Management and Activation / Data Acquisition and Preparation | **Team**: Gamma, Alpha
- **Top Contributors**: Ankireddy Raja Mouli (44) [Gamma], Dey Debdeep (14) [Alpha/Beta], Saurabh (11), Gajjar Rinkeshkumar (8) [Beta], Kumar Shubham (4)

#### spark-job-management
- **POD**: Data Acquisition and Preparation | **Team**: Alpha, Beta
- **Top Contributors**: Dey Debdeep (49) [Alpha/Beta], Pandit Kunal (9) [Alpha], Sargar Dadasaheb (6) [Kilo], Gajjar Rinkeshkumar (4) [Beta], Shelar Amol (3)

#### cortex-ui
- **POD**: Data In Use | **Team**: Tera
- **Top Contributors**: Rajpoot Mahendra Singh (12) [Tera], Killedar Sonali Bajirao (12) [Tera], Jadhav Dhanashri Niraj (10), Vikram Rajpurohit (7), Gaud Krishnakant Jagdish (7)

#### client-service
- **POD**: Data Acquisition and Preparation | **Team**: Beta
- **Top Contributors**: Bagchi Indrajit (28) [Beta], Dipak Bhoi (18), Varma Sandeep (14) [Beta], Borse Rajendra (12), Gajjar Rinkeshkumar (6) [Beta]

#### workpaper-service
- **POD**: Data In Use | **Team**: Giga
- **Top Contributors**: Patil Ajinkya U (16) [Giga], P ARUMUGAM (10) [Giga], Allada Srinivasarao (10), Singh Mukul Pratap (6), Nallamotu Teja Sri (5)

#### async-workflow-framework
- **POD**: Data Acquisition and Preparation / Data In Use | **Team**: Alpha, Giga
- **Top Contributors**: Kolhe Rakesh (25) [Alpha], Patil Ajinkya U (7) [Giga], Borse Rajendra (6), Santhosh Patnam (5), Jadhav Anurag (4) [Skyrockets]

#### sampling-service
- **POD**: Data In Use | **Team**: Giga
- **Top Contributors**: Santhosh Patnam (25), Shrivastava Rahul (16) [Giga], Rajendran Anbarasan (16) [Giga], Sekharamahanti Tarun Kumar (4) [Tera/Kilo], Kumbhalkar Mahesh (3) [Kilo]

#### localization-service
- **POD**: Omnia JE / Data Mgmt & Activation | **Team**: Justice League, Skyrockets
- **Top Contributors**: Bhat Abdul Hamid (4) [Justice League], Jadhav Anurag (3) [Skyrockets], Agrawal Sakshi (3) [Skyrockets], Ziparu Dipak (2), Dhage Priyanka (2) [Skyrockets]

#### scheduler-service
- **POD**: Data Acquisition and Preparation | **Team**: Alpha
- **Top Contributors**: Awasthi Harshal (7) [Alpha], Kaviya K J (6), Bhat Abdul Hamid (4) [Justice League], Padhi (3), Agrawal Sakshi (2) [Skyrockets]

#### cortexpy
- **POD**: Data Management and Activation / Data Acquisition and Preparation | **Team**: Delta, Beta
- **Top Contributors**: Bandi Melvin (12) [Delta], Sai Chimata Giridhar (10) [Beta], Kuderakar Chetan R (10) [Delta], Ganapathi Ekambaram (9), Somasundaram Thirunavukkarasu (7) [Delta]

#### analytic-notebooks
- **POD**: Data Acquisition and Preparation | **Team**: Beta
- **Top Contributors**: Sai Chimata Giridhar (15) [Beta], William Phillips (14), Gaikwad Manjusha (8) [Beta], Ramireddy (6), Bandi Melvin (6) [Delta]

### Key Cross-Repository Contributors

These contributors work across multiple repositories and are valuable resources for cross-functional issues:

| Contributor | Team | Repositories | Total Commits |
|-------------|------|--------------|---------------|
| Jadhav, Anurag | Skyrockets | 6 repos | 80+ |
| Awasthi, Harshal | Alpha | 5 repos | 75+ |
| Dey, Debdeep | Alpha/Beta | 2 repos | 63 |
| Bagchi, Indrajit | Beta | 2 repos | 49 |
| Sai, Chimata Giridhar | Beta | 3 repos | 35+ |
| Borse, Rajendra | (Cross-team) | 4 repos | 28+ |
| Gajjar, Rinkeshkumar | Beta | 4 repos | 26+ |

### Git Commands for Investigation

#### Clone a repository
```bash
git clone git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/{repo-name} ~/code/{repo-name}
```

#### Update existing repository
```bash
cd ~/code/{repo-name}
git fetch origin
git checkout master
git pull origin master
```

#### Checkout release branch
```bash
git fetch --all
git checkout RELEASE_{version}
git pull origin RELEASE_{version}
```

---

## Release Branch Strategy

### Current Releases
| Release | Status | Branch | Environments |
|---------|--------|--------|--------------|
| 9.5.x | **Production** | `RELEASE_9.5` | PROD, BCP, CNT1 |
| 9.6.x | Development | `develop` | DEV, QAS, STG2 |

### Investigation by Environment
When investigating issues, use the appropriate branch based on the environment:

| Environment | Release | Branch to Checkout |
|-------------|---------|-------------------|
| PROD, BCP, CNT1 | 9.5.x | `RELEASE_9.5` |
| STG | 9.5.x | `RELEASE_9.5` |
| STG2 | 9.6.x | `RELEASE_9.6` or `develop` |
| DEV, DEV1, DEV2 | 9.6.x | `develop` |
| QAS, QAS1, QAS2 | 9.6.x | `develop` |

### Release Branch Commands
```bash
# For PROD investigation (9.5.x)
cd ~/code/{repo-name}
git fetch origin
git checkout RELEASE_9.5
git pull origin RELEASE_9.5

# For DEV/QAS investigation (9.6.x)
cd ~/code/{repo-name}
git fetch origin
git checkout develop
git pull origin develop
```

---

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

| Env | App Insights | Resource Group | Log Analytics Workspace | LAW Resource Group | Subscription | Subscription ID |
|-----|--------------|----------------|------------------------|-------------------|--------------|-----------------|
| DEV | APPIN_CORTEX_APPLICATION_GENERAL_DEV | App-Cortex-AME-DEV-RG | npdamecortexlaw | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD | `1b5b460a-3534-4769-be45-8c3cc3a1eb69` |
| DEV1 | APPIN_CORTEX_APPLICATION_GENERAL_DEV1 | App-Cortex-AME-DEV1-RG | npdamecortexlaw | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD | `1b5b460a-3534-4769-be45-8c3cc3a1eb69` |
| DEV2 | APPIN_CORTEX_APPLICATION_GENERAL_DEV2 | App-Cortex-PaaS-AME-DEV2-RG | npdamecortexlaw | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD | `1b5b460a-3534-4769-be45-8c3cc3a1eb69` |
| QAS | APPIN_CORTEX_APPLICATION_GENERAL_QAS | App-Cortex-AME-QAS-RG | npdamecortexlaw | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD | `1b5b460a-3534-4769-be45-8c3cc3a1eb69` |
| QAS1 | APPIN_CORTEX_APPLICATION_GENERAL_QAS1 | App-Cortex-AME-QAS1-RG | npdamecortexlaw | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD | `1b5b460a-3534-4769-be45-8c3cc3a1eb69` |
| QAS2 | APPIN_CORTEX_APPLICATION_GENERAL_QAS2 | App-Cortex-PaaS-AME-QAS2-RG | npdamecortexlaw | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD | `1b5b460a-3534-4769-be45-8c3cc3a1eb69` |
| LOD | APPIN_CORTEX_APPLICATION_GENERAL_LOD | App-Cortex-AME-LOD-RG | npdamecortexlaw | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD | `1b5b460a-3534-4769-be45-8c3cc3a1eb69` |
| STG | APPIN_CORTEX_APPLICATION_GENERAL_STG | App-Cortex-AME-STG-RG | prdamecortexlaw | app-cortex-ame-prd-shared-rg | US_AUDIT_PROD | `7ce6ca13-2845-4f6a-9c2e-39675fc8c55e` |
| STG2 | APPIN_CORTEX_APPLICATION_GENERAL_STG2 | App-Cortex-PaaS-AME-STG2-RG | prdamecortexlaw | app-cortex-ame-prd-shared-rg | US_AUDIT_PROD | `7ce6ca13-2845-4f6a-9c2e-39675fc8c55e` |
| CNT1 | APPIN_CORTEX_APPLICATION_GENERAL_CNT1 | App-Cortex-AME-CNT1-RG | prdamecortexlaw | app-cortex-ame-prd-shared-rg | US_AUDIT_PROD | `7ce6ca13-2845-4f6a-9c2e-39675fc8c55e` |
| PRD | APPIN_CORTEX_APPLICATION_GENERAL_PRD | App-Cortex-AME-PRD-RG | prdamecortexlaw | app-cortex-ame-prd-shared-rg | US_AUDIT_PROD | `7ce6ca13-2845-4f6a-9c2e-39675fc8c55e` |
| BCP | APPIN_CORTEX_APPLICATION_GENERAL_BCP | App-Cortex-AME-BCP-RG | bcpamecortexlaw | App-Cortex-AME-BCP-Shared-RG | US_AUDIT_PROD | `7ce6ca13-2845-4f6a-9c2e-39675fc8c55e` |

### EMA (Europe/Middle East/Africa) Environments

| Env | App Insights | Resource Group | Log Analytics Workspace | LAW Resource Group | Subscription | Subscription ID |
|-----|--------------|----------------|------------------------|-------------------|--------------|-----------------|
| INT | APPIN_CORTEX_APPLICATION_GENERAL_INT | App-Cortex-PaaS-EMA-INT-RG | npdemacortexlaw | app-cortex-ema-npd-shared-rg | US_AUDIT_PREPROD | `1b5b460a-3534-4769-be45-8c3cc3a1eb69` |
| STG | APPIN_CORTEX_APPLICATION_GENERAL_STG | App-Cortex-PaaS-EMA-STG-RG | npdemacortexlaw | app-cortex-ema-npd-shared-rg | US_AUDIT_PREPROD | `1b5b460a-3534-4769-be45-8c3cc3a1eb69` |
| PRD | APPIN_CORTEX_APPLICATION_GENERAL_PRD | App-Cortex-PaaS-EMA-PRD-RG | prdemacortexlaw | app-cortex-ema-prd-shared-rg | US_AUDIT_PROD | `7ce6ca13-2845-4f6a-9c2e-39675fc8c55e` |
| BCP | APPIN_CORTEX_APPLICATION_GENERAL_BCP | App-Cortex-PaaS-EMA-BCP-RG | bcpemacortexlaw | app-cortex-ema-bcp-shared-rg | US_AUDIT_PROD | `7ce6ca13-2845-4f6a-9c2e-39675fc8c55e` |

### APAC (Asia Pacific) Environments

| Env | App Insights | Resource Group | Log Analytics Workspace | LAW Resource Group | Subscription | Subscription ID |
|-----|--------------|----------------|------------------------|-------------------|--------------|-----------------|
| STG | APPIN_CORTEX_APPLICATION_GENERAL_STG | App-Cortex-PaaS-APA-STG-RG | prdapacortexlaw | App-Cortex-APA-PRD-Shared-RG | US_AUDIT_APA | `b2fcc9cc-5757-42d3-980c-d92d66bab682` |
| PRD | APPIN_CORTEX_APPLICATION_GENERAL_PRD | App-Cortex-PaaS-APA-PRD-RG | prdapacortexlaw | App-Cortex-APA-PRD-Shared-RG | US_AUDIT_APA | `b2fcc9cc-5757-42d3-980c-d92d66bab682` |
| BCP | APPIN_CORTEX_APPLICATION_GENERAL_BCP | App-Cortex-PaaS-APA-BCP-RG | bcpapacortexlaw | App-Cortex-APA-BCP-Shared-RG | US_AUDIT_APA | `b2fcc9cc-5757-42d3-980c-d92d66bab682` |

### Subscription Switching for Log Analysis

**IMPORTANT**: Before querying logs for EMA or APA regions, you must switch to the correct Azure subscription.

#### Quick Reference

| Region | Subscription | Subscription ID | Switch Command |
|--------|--------------|-----------------|----------------|
| AME (Americas) Non-Prod | US_AUDIT_PREPROD | `1b5b460a-3534-4769-be45-8c3cc3a1eb69` | `az account set -s 1b5b460a-3534-4769-be45-8c3cc3a1eb69` |
| AME (Americas) Prod | US_AUDIT_PROD | `7ce6ca13-2845-4f6a-9c2e-39675fc8c55e` | `az account set -s 7ce6ca13-2845-4f6a-9c2e-39675fc8c55e` |
| EMA Non-Prod | US_AUDIT_PREPROD | `1b5b460a-3534-4769-be45-8c3cc3a1eb69` | `az account set -s 1b5b460a-3534-4769-be45-8c3cc3a1eb69` |
| EMA Prod | US_AUDIT_PROD | `7ce6ca13-2845-4f6a-9c2e-39675fc8c55e` | `az account set -s 7ce6ca13-2845-4f6a-9c2e-39675fc8c55e` |
| **APA (Asia Pacific)** | US_AUDIT_APA | `b2fcc9cc-5757-42d3-980c-d92d66bab682` | `az account set -s b2fcc9cc-5757-42d3-980c-d92d66bab682` |

#### Example: Query APA Production Logs

```bash
# Step 1: Switch to APA subscription
az account set -s b2fcc9cc-5757-42d3-980c-d92d66bab682

# Step 2: Verify subscription
az account show --query "{Name:name, ID:id}" -o table

# Step 3: Query Log Analytics
az monitor log-analytics query \
  --workspace prdapacortexlaw \
  --analytics-query "AppExceptions | where TimeGenerated > ago(1h) | take 10"
```

#### Example: Query EMA Production Logs

```bash
# Step 1: Switch to EMA Prod subscription
az account set -s 7ce6ca13-2845-4f6a-9c2e-39675fc8c55e

# Step 2: Query Log Analytics
az monitor log-analytics query \
  --workspace prdemacortexlaw \
  --analytics-query "AppExceptions | where TimeGenerated > ago(1h) | take 10"
```

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

---

## Team Information (PI21)

### Current Program Increment
- **PI21** (Program Increment 21)
- **Future Release**: 9.6

### Organizational Structure
```
Audit Cortex 2
└── Omnia Data
    ├── Omnia Data Acquisition
    │   └── Galileo
    ├── Omnia Data Management
    │   ├── Data Acquisition and Preparation (POD)
    │   │   ├── Alpha
    │   │   ├── Beta
    │   │   ├── Megatron
    │   │   └── Support
    │   └── Data Management and Activation (POD)
    │       ├── Delta
    │       ├── Gamma
    │       └── Skyrockets
    ├── Omnia Data Automation
    │   ├── Omnia JE (POD)
    │   │   ├── Exa
    │   │   ├── Jupiter
    │   │   ├── Justice League
    │   │   ├── Neptune
    │   │   ├── Peta
    │   │   ├── Saturn
    │   │   ├── Utopia
    │   │   └── Support
    │   └── Data In Use (POD)
    │       ├── Giga
    │       ├── Kilo
    │       ├── Peta
    │       └── Tera
    ├── Core Data Engineering
    ├── Health Monitoring
    └── SpaceBots
```

### Teams by POD

#### Data Acquisition and Preparation
| Team | Area Path |
|------|-----------|
| Alpha | `Audit Cortex 2\Omnia Data\Omnia Data Management\Data Acquisition and Preparation\Alpha` |
| Beta | `Audit Cortex 2\Omnia Data\Omnia Data Management\Data Acquisition and Preparation\Beta` |
| Megatron | `Audit Cortex 2\Omnia Data\Omnia Data Management\Data Acquisition and Preparation\Megatron` |
| Support | `Audit Cortex 2\Omnia Data\Omnia Data Management\Data Acquisition and Preparation\Support` |

#### Data Management and Activation
| Team | Area Path |
|------|-----------|
| Delta | `Audit Cortex 2\Omnia Data\Omnia Data Management\Data Management and Activation\Delta` |
| Gamma | `Audit Cortex 2\Omnia Data\Omnia Data Management\Data Management and Activation\Gamma` |
| Skyrockets | `Audit Cortex 2\Omnia Data\Omnia Data Management\Data Management and Activation\Skyrockets` |

#### Omnia JE
| Team | Area Path |
|------|-----------|
| Exa | `Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Exa` |
| Jupiter | `Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Jupiter` |
| Justice League | `Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Justice League` |
| Neptune | `Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Neptune` |
| Peta | `Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Peta` |
| Saturn | `Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Saturn` |
| Utopia | `Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Utopia` |
| Support | `Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Support` |

#### Data In Use
| Team | Area Path |
|------|-----------|
| Giga | `Audit Cortex 2\Omnia Data\Omnia Data Automation\Data In Use\Giga` |
| Kilo | `Audit Cortex 2\Omnia Data\Omnia Data Automation\Data In Use\Kilo` |
| Peta | `Audit Cortex 2\Omnia Data\Omnia Data Automation\Data In Use\Peta` |
| Tera | `Audit Cortex 2\Omnia Data\Omnia Data Automation\Data In Use\Tera` |

#### Other Teams
| Team | Area Path |
|------|-----------|
| Galileo | `Audit Cortex 2\Omnia Data\Omnia Data Acquisition\Galileo` |
| Core Data Engineering | `Audit Cortex 2\Omnia Data\Core Data Engineering` |
| Health Monitoring | `Audit Cortex 2\Omnia Data\Health Monitoring` |
| SpaceBots | `Audit Cortex 2\Omnia Data\SpaceBots` |
