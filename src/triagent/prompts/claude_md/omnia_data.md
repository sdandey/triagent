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

## Release Pipelines

### Pipeline Naming Conventions

Omnia Data release pipelines follow consistent naming patterns. Use these patterns to identify pipelines (IDs change frequently).

| Prefix | Category | Description |
|--------|----------|-------------|
| `Omnia-Data-deploy-helm-` | Helm | AKS/Kubernetes deployments |
| `Omnia-Data-deploy-databricks-infra-` | Databricks Infra | Databricks workspace infrastructure |
| `Omnia-Data-deploy-platform-notebooks-` | Notebooks | Databricks notebook deployments |
| `Omnia-Data-deploy-appconfiguration-` | App Config | Azure App Configuration |
| `Omnia-Data-deploy-content-library-` | Content Library | Shared content artifacts |
| `Omnia-Data-datamangement-services-` | Data Management | cortex-datamanagement-services |
| `Omnia-Data-deploy-wj&fa-` | WJ&FA | Workpaper/FA deployments |
| `Omnia-Data-integration-services-` | Integration | Integration service |
| `OmniaData-je-deploy-` | JE Deploy | JE Analytics API/Jobs |
| `OmniaData-je-fdr-` | JE FDR | JE Full Data Refresh |

### Version Patterns

| Version | Pattern | Status | Use Case |
|---------|---------|--------|----------|
| 9.5 | `Release-9.5$` or `-9.5$` | **Production** | Current live release |
| 9.5.1 | `Release-9.5.1$` | Production Hotfix | Post-release fixes |
| 9.5.1.200 | `-9.5.1.200$` | Specific Hotfix | Targeted fixes |
| 9.6 WIP | `Release.9.6.WIP$` | **Development** | Next release development |
| 9.4.x | `-9.4$` or `-9.4.1$` | Legacy | Archived |

### Current Production Pipelines (9.5.x)

| Category | Pipeline Name | Purpose |
|----------|---------------|---------|
| Helm | `Omnia-Data-deploy-helm-9.5` | AKS/Helm deployments |
| Helm | `Omnia-Data-deploy-helm-9.5.1` | Helm (9.5.1 hotfix) |
| Helm | `Omnia-Data-deploy-helm-9.5.1.200` | Helm (9.5.1.200 hotfix) |
| Data Mgmt | `Omnia-Data-datamangement-services-Release-9.5` | Data Management Services |
| Data Mgmt | `Omnia-Data-datamangement-services-Release-9.5.1` | Data Management (9.5.1) |
| App Config | `Omnia-Data-deploy-appconfiguration-9.5` | App Configuration |
| App Config | `Omnia-Data-deploy-appconfiguration-9.5.1` | App Configuration (9.5.1) |
| DBX Infra | `Omnia-Data-deploy-databricks-infra-Release-9.5` | Databricks Infrastructure |
| DBX Infra | `Omnia-Data-deploy-databricks-infra-Release-9.5.1` | DBX Infra (9.5.1) |
| DBX Infra | `Omnia-Data-deploy-databricks-infra-Release-9.5.1.200` | DBX Infra (9.5.1.200) |
| Notebooks | `Omnia-Data-deploy-platform-notebooks-Release-9.5` | Platform Notebooks |
| Notebooks | `Omnia-Data-deploy-platform-notebooks-Release-9.5.1` | Notebooks (9.5.1) |
| Notebooks | `Omnia-Data-deploy-platform-notebooks-Release-9.5.1.200` | Notebooks (9.5.1.200) |
| Content | `Omnia-Data-deploy-content-library-artifacts-9.5` | Content Library |
| Content | `Omnia-Data-deploy-content-library-artifacts-9.5.1` | Content Library (9.5.1) |
| WJ&FA | `Omnia-Data-deploy-wj&fa-9.5` | Workpaper/FA |
| Integration | `Omnia-Data-integration-services-9.5` | Integration Services |
| JE Deploy | `OmniaData-je-deploy-analyticsapi-analyticsjobs-Release-9.5` | JE Analytics API |
| JE Deploy | `OmniaData-je-deploy-analyticsapi-analyticsjobs-Release-9.5.1` | JE Analytics (9.5.1) |
| JE Deploy | `OmniaData-je-deploy-analyticsapi-analyticsjobs-Hotfix-9.5.1.100` | JE Analytics Hotfix |
| JE FDR | `OmniaData-je-fdr-all-Release-9.5` | JE Full Data Refresh |

### Development Pipelines (9.6 WIP)

| Category | Pipeline Name |
|----------|---------------|
| Helm | `Omnia-Data-deploy-helm-Release-9.6 WIP` |
| Data Mgmt | `Omnia-Data-datamangement-services-Release 9.6 WIP` |
| App Config | `Omnia-Data-deploy-appconfiguration-Release -9.6 WIP` |
| DBX Infra | `Omnia-Data-deploy-databricks-infra-Release 9.6 WIP` |
| Notebooks | `Omnia-Data-deploy-platform-notebooks-Release 9.6 WIP` |
| Content | `Omnia-Data-deploy-content-library-artifacts-Release  9.6 WIP` |
| WJ&FA | `Omnia-Data-deploy-wj&fa-Release 9.6 WIP` |
| Integration | `Omnia-Data-integration-services -Release 9.6 WIP` |
| JE Deploy | `OmniaData-je-deploy-analyticsapi-analyticsjobs-Release 9.6 WIP` |
| JE FDR | `OmniaData-je-fdr-all-Release 9.6 WIP` |

### Deployment Stages

Standard deployment stages across all Omnia Data pipelines:

| Stage | Type | Rank | Description |
|-------|------|------|-------------|
| AME DEV2, DEV, DEV1 | Development | 1-4 | Development environments |
| AME QAS2, QAS, QAS1 | QA | 3-5 | Quality assurance |
| LOD-* | Load Test | 7-9 | Performance/cost testing |
| AME STG2, STG | Staging | 11-12 | Pre-production |
| EMA STG, APA STG | Staging | 13-14 | Regional staging |
| AME CNT1 | Continuity | 16 | DR testing |
| AME PRD | **Production** | 17 | Americas production |
| EMA PRD | **Production** | 18 | EMA production |
| APA PRD | **Production** | 19 | APA production |
| AME BCP, EMA BCP, APA BCP | BCP | 20-22 | Disaster recovery |
| EMA INT | Integration | 25 | EMA integration |
| TOSCA-* | Automation | 26-27 | Test automation |

### Pipeline Query Commands

#### List all Omnia Data pipelines
```bash
az pipelines release definition list \
  --organization https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  --query "[?contains(name, 'Omnia-Data') || contains(name, 'OmniaData')].{Name:name, ID:id}" \
  -o table
```

#### Find pipelines by category (e.g., helm)
```bash
az pipelines release definition list \
  --organization https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  --query "[?contains(name, 'deploy-helm')].{Name:name, ID:id}" \
  -o table
```

#### Find pipelines by version (e.g., 9.5)
```bash
az pipelines release definition list \
  --organization https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  --query "[?contains(name, '9.5') && (contains(name, 'Omnia-Data') || contains(name, 'OmniaData'))].{Name:name, ID:id}" \
  -o table
```

#### Get pipeline stages
```bash
az pipelines release definition show \
  --organization https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  --name "<PIPELINE_NAME>" \
  --query "{Name:name, Environments:environments[].name}" \
  -o json
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

| Env | App Insights | Resource Group | Log Analytics Workspace | Workspace ID | LAW Resource Group | Subscription | Subscription ID |
|-----|--------------|----------------|------------------------|--------------|-------------------|--------------|-----------------|
| DEV | APPIN_CORTEX_APPLICATION_GENERAL_DEV | App-Cortex-AME-DEV-RG | npdamecortexlaw | `874aa8fb-6d29-4521-920f-63ac7168404e` | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD | `d7ac9c0b-155b-42a8-9d7d-87e883f82d5d` |
| DEV1 | APPIN_CORTEX_APPLICATION_GENERAL_DEV1 | App-Cortex-AME-DEV1-RG | npdamecortexlaw | `874aa8fb-6d29-4521-920f-63ac7168404e` | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD | `d7ac9c0b-155b-42a8-9d7d-87e883f82d5d` |
| DEV2 | APPIN_CORTEX_APPLICATION_GENERAL_DEV2 | App-Cortex-PaaS-AME-DEV2-RG | npdamecortexlaw | `874aa8fb-6d29-4521-920f-63ac7168404e` | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD | `d7ac9c0b-155b-42a8-9d7d-87e883f82d5d` |
| QAS | APPIN_CORTEX_APPLICATION_GENERAL_QAS | App-Cortex-AME-QAS-RG | npdamecortexlaw | `874aa8fb-6d29-4521-920f-63ac7168404e` | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD | `d7ac9c0b-155b-42a8-9d7d-87e883f82d5d` |
| QAS1 | APPIN_CORTEX_APPLICATION_GENERAL_QAS1 | App-Cortex-AME-QAS1-RG | npdamecortexlaw | `874aa8fb-6d29-4521-920f-63ac7168404e` | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD | `d7ac9c0b-155b-42a8-9d7d-87e883f82d5d` |
| QAS2 | APPIN_CORTEX_APPLICATION_GENERAL_QAS2 | App-Cortex-PaaS-AME-QAS2-RG | npdamecortexlaw | `874aa8fb-6d29-4521-920f-63ac7168404e` | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD | `d7ac9c0b-155b-42a8-9d7d-87e883f82d5d` |
| LOD | APPIN_CORTEX_APPLICATION_GENERAL_LOD | App-Cortex-AME-LOD-RG | npdamecortexlaw | `874aa8fb-6d29-4521-920f-63ac7168404e` | App-Cortex-AME-NPD-Shared-RG | US_AUDIT_PREPROD | `d7ac9c0b-155b-42a8-9d7d-87e883f82d5d` |
| STG | APPIN_CORTEX_APPLICATION_GENERAL_STG | App-Cortex-AME-STG-RG | prdamecortexlaw | `ed9e6912-0544-405b-921b-f2d6aad2155e` | app-cortex-ame-prd-shared-rg | US_AUDIT_PROD | `8c71ef53-4473-4862-af36-bae6e40451b2` |
| STG2 | APPIN_CORTEX_APPLICATION_GENERAL_STG2 | App-Cortex-PaaS-AME-STG2-RG | prdamecortexlaw | `ed9e6912-0544-405b-921b-f2d6aad2155e` | app-cortex-ame-prd-shared-rg | US_AUDIT_PROD | `8c71ef53-4473-4862-af36-bae6e40451b2` |
| CNT1 | APPIN_CORTEX_APPLICATION_GENERAL_CNT1 | App-Cortex-AME-CNT1-RG | prdamecortexlaw | `ed9e6912-0544-405b-921b-f2d6aad2155e` | app-cortex-ame-prd-shared-rg | US_AUDIT_PROD | `8c71ef53-4473-4862-af36-bae6e40451b2` |
| PRD | APPIN_CORTEX_APPLICATION_GENERAL_PRD | App-Cortex-AME-PRD-RG | prdamecortexlaw | `ed9e6912-0544-405b-921b-f2d6aad2155e` | app-cortex-ame-prd-shared-rg | US_AUDIT_PROD | `8c71ef53-4473-4862-af36-bae6e40451b2` |
| BCP | APPIN_CORTEX_APPLICATION_GENERAL_BCP | App-Cortex-AME-BCP-RG | bcpamecortexlaw | `ef540bd5-ce75-4aac-8d29-7aa576b9d537` | App-Cortex-AME-BCP-Shared-RG | US_AUDIT_PROD | `8c71ef53-4473-4862-af36-bae6e40451b2` |

### EMA (Europe/Middle East/Africa) Environments

| Env | App Insights | Resource Group | Log Analytics Workspace | Workspace ID | LAW Resource Group | Subscription | Subscription ID |
|-----|--------------|----------------|------------------------|--------------|-------------------|--------------|-----------------|
| INT | APPIN_CORTEX_APPLICATION_GENERAL_INT | App-Cortex-PaaS-EMA-INT-RG | icortexjeemala | `8c9be877-4f75-45ed-b34a-e067a87918c0` | app-cortex-paas-ema-int-rg | US-AZSUB-EMA-AUD-NPD-01 | `429c67ab-6761-4617-a512-a4743395cede` |
| STG | APPIN_CORTEX_APPLICATION_GENERAL_STG | App-Cortex-PaaS-EMA-STG-RG | scortexjeemala | `9cb4fe2f-645d-45ae-83c0-fe5b88309aef` | app-cortex-paas-ema-stg-rg | US-AZSUB-EMA-AUD-PRD-01 | `62c1dd5c-d918-4a4d-b0ee-18d5e7d5071b` |
| PRD | APPIN_CORTEX_APPLICATION_GENERAL_PRD | App-Cortex-PaaS-EMA-PRD-RG | prdemacortexlaw | `b3f751c4-5cce-4caa-a3fb-eccbe019c661` | App-Cortex-EMA-PRD-Shared-RG | US-AZSUB-EMA-AUD-PRD-01 | `62c1dd5c-d918-4a4d-b0ee-18d5e7d5071b` |
| BCP | APPIN_CORTEX_APPLICATION_GENERAL_BCP | App-Cortex-PaaS-EMA-BCP-RG | bcortexjeemala | `1ef0ab98-6954-4099-9fd8-2887af05a314` | App-Cortex-PaaS-EMA-BCP-RG | US-AZSUB-EMA-AUD-PRD-01 | `62c1dd5c-d918-4a4d-b0ee-18d5e7d5071b` |

### APAC (Asia Pacific) Environments

| Env | App Insights | Resource Group | Log Analytics Workspace | Workspace ID | LAW Resource Group | Subscription | Subscription ID |
|-----|--------------|----------------|------------------------|--------------|-------------------|--------------|-----------------|
| STG | APPIN_CORTEX_APPLICATION_GENERAL_STG | App-Cortex-PaaS-APA-STG-RG | prdapacortexlaw | `d333bffc-5984-4bcd-a600-064988e7e2ec` | App-Cortex-APA-PRD-Shared-RG | US_AUDIT_APA | `b2fcc9cc-5757-42d3-980c-d92d66bab682` |
| PRD | APPIN_CORTEX_APPLICATION_GENERAL_PRD | App-Cortex-PaaS-APA-PRD-RG | prdapacortexlaw | `d333bffc-5984-4bcd-a600-064988e7e2ec` | App-Cortex-APA-PRD-Shared-RG | US_AUDIT_APA | `b2fcc9cc-5757-42d3-980c-d92d66bab682` |
| BCP | APPIN_CORTEX_APPLICATION_GENERAL_BCP | App-Cortex-PaaS-APA-BCP-RG | bcpapacortexlaw | *TBD* | App-Cortex-APA-BCP-Shared-RG | US_AUDIT_APA | `b2fcc9cc-5757-42d3-980c-d92d66bab682` |

### Subscription Switching for Log Analysis

**IMPORTANT**: Before querying logs for EMA or APA regions, you must switch to the correct Azure subscription.

#### Quick Reference

| Region | Subscription | Subscription ID | Switch Command |
|--------|--------------|-----------------|----------------|
| AME (Americas) Non-Prod | US_AUDIT_PREPROD | `d7ac9c0b-155b-42a8-9d7d-87e883f82d5d` | `az account set -s d7ac9c0b-155b-42a8-9d7d-87e883f82d5d` |
| AME (Americas) Prod | US_AUDIT_PROD | `8c71ef53-4473-4862-af36-bae6e40451b2` | `az account set -s 8c71ef53-4473-4862-af36-bae6e40451b2` |
| **EMA Non-Prod** | US-AZSUB-EMA-AUD-NPD-01 | `429c67ab-6761-4617-a512-a4743395cede` | `az account set -s 429c67ab-6761-4617-a512-a4743395cede` |
| **EMA Prod** | US-AZSUB-EMA-AUD-PRD-01 | `62c1dd5c-d918-4a4d-b0ee-18d5e7d5071b` | `az account set -s 62c1dd5c-d918-4a4d-b0ee-18d5e7d5071b` |
| **APA (Asia Pacific)** | US_AUDIT_APA | `b2fcc9cc-5757-42d3-980c-d92d66bab682` | `az account set -s b2fcc9cc-5757-42d3-980c-d92d66bab682` |

#### Example: Query APA Production Logs

```bash
# Step 1: Switch to APA subscription
az account set -s b2fcc9cc-5757-42d3-980c-d92d66bab682

# Step 2: Verify subscription
az account show --query "{Name:name, ID:id}" -o table

# Step 3: Query Log Analytics (use Workspace ID, not name)
az monitor log-analytics query \
  --workspace d333bffc-5984-4bcd-a600-064988e7e2ec \
  --analytics-query "AppExceptions | where TimeGenerated > ago(1h) | take 10"
```

> **Note**: Azure CLI now requires the Workspace ID (Customer ID/GUID) instead of workspace name for `az monitor log-analytics query`. Find the Workspace ID in the telemetry tables above.

#### Example: Query EMA Production Logs

```bash
# Step 1: Switch to EMA Prod subscription
az account set -s 62c1dd5c-d918-4a4d-b0ee-18d5e7d5071b

# Step 2: Query Log Analytics (use Workspace ID)
az monitor log-analytics query \
  --workspace b3f751c4-5cce-4caa-a3fb-eccbe019c661 \
  --analytics-query "AppExceptions | where TimeGenerated > ago(1h) | take 10"
```

#### Example: Query AME Production Logs

```bash
# Step 1: Switch to AME Prod subscription
az account set -s 8c71ef53-4473-4862-af36-bae6e40451b2

# Step 2: Query Log Analytics (use Workspace ID)
az monitor log-analytics query \
  --workspace ed9e6912-0544-405b-921b-f2d6aad2155e \
  --analytics-query "AppExceptions | where TimeGenerated > ago(1h) | take 10"
```

#### Example: Query AME Non-Prod Logs (DEV/QAS)

```bash
# Step 1: Switch to AME Non-Prod subscription
az account set -s d7ac9c0b-155b-42a8-9d7d-87e883f82d5d

# Step 2: Query Log Analytics (use Workspace ID)
az monitor log-analytics query \
  --workspace 874aa8fb-6d29-4521-920f-63ac7168404e \
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

## Clarifying Questions Guidelines (PROACTIVE MODE)

You MUST ask clarifying questions BEFORE starting any investigation or telemetry gathering.
Do NOT proceed with assumptions - ask first to avoid wasted API calls and incorrect results.

### When to Ask (ALWAYS before these actions):
- User says "investigate", "gather telemetry", "check logs", "look into", "debug"
- User mentions a service without specifying environment
- User requests exception/error analysis
- Any request involving Log Analytics or Application Insights

### Required Information to Gather:

1. **Environment** (REQUIRED): Which environment?
   - AME Non-Prod: DEV, DEV1, DEV2, QAS, QAS1, QAS2, LOD
   - AME Prod: STG, STG2, CNT1, PRD, BCP

2. **Timeframe** (REQUIRED): What time range?
   - Last 1 hour (default for active issues)
   - Last 24 hours
   - Last 7 days
   - Custom range (ask for specific dates)

3. **Service** (if not specified): Which CloudRoleName/service?
   - Reference the Service Names table above

### Example:
User: "Investigate the staging service errors"
Agent: [Uses AskUserQuestion tool]
  Question 1: "Which environment?" Options: DEV, QAS, STG, PRD, etc.
  Question 2: "What timeframe?" Options: Last 1 hour, Last 24 hours, etc.
Then uses the correct Log Analytics workspace from the telemetry config.

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

