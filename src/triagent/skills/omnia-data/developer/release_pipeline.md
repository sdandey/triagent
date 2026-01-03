---
name: release_pipeline
display_name: "Release Pipeline"
description: "Identify and query Omnia Data release pipelines by name patterns"
version: "1.0.0"
tags: [pipelines, release, deployment, omnia-data]
requires: [ado_basics]
subagents: []
tools:
  - Bash
triggers:
  - "release.*pipeline"
  - "deploy.*9\\.[456]"
  - "pipeline.*omnia"
  - "which pipeline"
  - "find pipeline"
---

## Release Pipeline Identification

This skill helps identify and query Omnia Data release pipelines using name patterns rather than IDs (which change frequently).

### Pipeline Naming Conventions

Omnia Data pipelines follow these naming patterns:

| Prefix | Category | Example |
|--------|----------|---------|
| `Omnia-Data-deploy-helm-` | AKS/Kubernetes deployments | `Omnia-Data-deploy-helm-9.5` |
| `Omnia-Data-deploy-databricks-infra-` | Databricks infrastructure | `Omnia-Data-deploy-databricks-infra-Release-9.5` |
| `Omnia-Data-deploy-platform-notebooks-` | Databricks notebooks | `Omnia-Data-deploy-platform-notebooks-Release-9.5` |
| `Omnia-Data-deploy-appconfiguration-` | Azure App Configuration | `Omnia-Data-deploy-appconfiguration-9.5` |
| `Omnia-Data-deploy-content-library-` | Content library artifacts | `Omnia-Data-deploy-content-library-artifacts-9.5` |
| `Omnia-Data-datamangement-services-` | Data Management Services | `Omnia-Data-datamangement-services-Release-9.5` |
| `Omnia-Data-deploy-wj&fa-` | Workpaper/FA | `Omnia-Data-deploy-wj&fa-9.5` |
| `Omnia-Data-integration-services-` | Integration Services | `Omnia-Data-integration-services-9.5` |
| `OmniaData-je-deploy-` | JE Analytics API/Jobs | `OmniaData-je-deploy-analyticsapi-analyticsjobs-Release-9.5` |
| `OmniaData-je-fdr-` | JE Full Data Refresh | `OmniaData-je-fdr-all-Release-9.5` |

### Version Patterns

| Version | Pattern | Status |
|---------|---------|--------|
| 9.5 | `Release-9.5$` or `-9.5$` | **Production** |
| 9.5.1 | `Release-9.5.1$` or `-9.5.1$` | Production Hotfix |
| 9.5.1.200 | `-9.5.1.200$` | Specific Hotfix |
| 9.6 WIP | `Release.9.6.WIP$` or `9.6.WIP$` | **Development** |
| 9.4.x | `-9.4$` or `-9.4.1$` | Legacy (archived) |

### Regex Patterns for Pipeline Matching

```regex
# Match any Omnia Data pipeline
^(Omnia-Data|OmniaData)-

# Match specific categories
helm:           ^Omnia-Data-deploy-helm-
databricks:     ^Omnia-Data-deploy-databricks-infra-
notebooks:      ^Omnia-Data-deploy-platform-notebooks-
appconfig:      ^Omnia-Data-deploy-appconfiguration-
content:        ^Omnia-Data-deploy-content-library-
datamanagement: ^Omnia-Data-datamangement-services-
wjfa:           ^Omnia-Data-deploy-wj&fa-
integration:    ^Omnia-Data-integration-services-
je-deploy:      ^OmniaData-je-deploy-
je-fdr:         ^OmniaData-je-fdr-

# Match versions
production:     Release-9\.5$
hotfix:         Release-9\.5\.1
development:    Release.9\.6.WIP$
```

### Clarifying Questions

**IMPORTANT**: When a user asks about pipelines without providing specific details, use AskUserQuestion to gather:

1. **Version** (Required)
   - 9.5 Production (current live)
   - 9.5.1 Hotfix
   - 9.6 Development (WIP)

2. **Category** (Required if investigating specific pipeline)
   - helm (AKS deployments)
   - databricks-infra (DBX infrastructure)
   - platform-notebooks (DBX notebooks)
   - appconfiguration (App Config)
   - content-library (shared content)
   - datamangement-services (Data Management)
   - wj&fa (Workpaper/FA)
   - integration-services
   - je-deploy (JE Analytics)
   - je-fdr (JE Full Data Refresh)

3. **Environment** (If checking deployment status)
   - DEV, DEV1, DEV2 (Development)
   - QAS, QAS1, QAS2 (QA)
   - LOD (Load Testing)
   - STG, STG2 (Staging)
   - PRD (Production)
   - CNT1 (Continuity)
   - BCP (Disaster Recovery)

4. **Region** (If multi-region)
   - AME (Americas)
   - EMA (Europe/Middle East/Africa)
   - APA (Asia Pacific)

### Azure CLI Commands

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
  --query "[?contains(name, '9.5')].{Name:name, ID:id}" \
  -o table | grep -E "Omnia-Data|OmniaData"
```

#### Get pipeline details (stages/environments)
```bash
az pipelines release definition show \
  --organization https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  --name "Omnia-Data-deploy-helm-9.5" \
  --query "{Name:name, Environments:environments[].name}" \
  -o json
```

#### List recent releases for a pipeline
```bash
az pipelines release list \
  --organization https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  --definition-id <PIPELINE_ID> \
  --top 10 \
  -o table
```

### Investigation Workflow

1. **Identify the Pipeline**
   - Ask clarifying questions if user doesn't specify version/category
   - Use regex patterns to match pipeline name
   - Query ADO to find pipeline by name pattern

2. **Get Pipeline Status**
   - List recent releases
   - Check deployment status per environment
   - Identify failed stages

3. **Analyze Issues**
   - Get release details for specific failures
   - Review deployment logs
   - Check environment-specific issues

4. **Report Findings**
   - Summarize pipeline status
   - List affected environments
   - Provide remediation steps

### Common Issues by Category

| Category | Common Issues |
|----------|---------------|
| helm | AKS node issues, helm chart errors, image pull failures |
| databricks-infra | Workspace provisioning, cluster issues, permissions |
| platform-notebooks | Notebook deployment, library installation |
| datamangement-services | App Service deployment, configuration errors |
| je-deploy | Analytics job failures, API deployment issues |
| je-fdr | Full data refresh timeouts, data processing errors |
