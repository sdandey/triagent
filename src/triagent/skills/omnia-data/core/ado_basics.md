---
name: ado_basics
display_name: "Azure DevOps Basics"
description: "Core Azure DevOps navigation, work item access, and repository operations"
version: "1.1.0"
tags: [ado, core, work-items, repositories]
requires: []
subagents: []
tools:
  - mcp__azure-devops__get_work_item
  - mcp__azure-devops__list_work_items
  - mcp__azure-devops__search_work_items
  - mcp__azure-devops__list_repositories
  - mcp__azure-devops__get_repository
  - mcp__azure-devops__get_file_content
  - Bash
triggers: []
---

## Azure DevOps Core Operations

You have access to Azure DevOps MCP tools and Azure CLI commands for work item and repository operations.

### Organization Context

| Setting | Value |
|---------|-------|
| **Organization** | `https://dev.azure.com/symphonyvsts` |
| **Project** | `Audit Cortex 2` |

---

## Work Item Operations

### MCP Tools (Preferred for Simple Operations)

- `mcp__azure-devops__get_work_item` - Fetch work item by ID
- `mcp__azure-devops__list_work_items` - List with filtering
- `mcp__azure-devops__search_work_items` - WIQL-based searches

### Azure CLI Commands

#### Read Operations

```bash
# Get work item details
az boards work-item show \
  --org https://dev.azure.com/symphonyvsts \
  --id {WORK_ITEM_ID} \
  -o json

# List work items with query
az boards query \
  --org https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  --wiql "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.WorkItemType] = 'Defect' AND [System.State] = 'New'" \
  -o json

# Get work item relations (parent/child links)
az boards work-item show --id {ID} -o json | jq '.relations'
```

#### Create Operations

```bash
# Create a new work item
az boards work-item create \
  --org https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  --type "Defect" \
  --title "Work Item Title" \
  --area "Audit Cortex 2\\Omnia Data\\..." \
  --iteration "Audit Cortex 2\\Program Increment 22" \
  --fields "Microsoft.VSTS.Common.Severity=2 - High" \
           "Microsoft.VSTS.Common.Priority=2"
```

#### Update Operations

```bash
# Update work item fields
az boards work-item update \
  --org https://dev.azure.com/symphonyvsts \
  --id {WORK_ITEM_ID} \
  --fields "System.State=Active" \
           "System.AssignedTo=user@domain.com"

# Add relation (parent link)
az boards work-item relation add \
  --org https://dev.azure.com/symphonyvsts \
  --id {CHILD_ID} \
  --relation-type "Parent" \
  --target-id {PARENT_ID}
```

### REST API (For HTML Content)

**Important**: Use REST API with JSON payload for HTML-formatted fields (Description, Repro Steps, etc.) as az CLI has escaping issues.

```bash
# Get access token
PAT=$(az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv)

# Create work item with HTML fields
curl -s -X POST \
  "https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_apis/wit/workitems/\$Defect?api-version=7.0" \
  -H "Content-Type: application/json-patch+json" \
  -H "Authorization: Bearer $PAT" \
  -d @/tmp/workitem.json

# Update work item with HTML fields
curl -s -X PATCH \
  "https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_apis/wit/workitems/{ID}?api-version=7.0" \
  -H "Content-Type: application/json-patch+json" \
  -H "Authorization: Bearer $PAT" \
  -d @/tmp/update.json
```

#### JSON Payload Format

```json
[
  { "op": "add", "path": "/fields/System.Title", "value": "Title" },
  { "op": "add", "path": "/fields/System.Description", "value": "<div>HTML content</div>" },
  { "op": "add", "path": "/fields/Microsoft.VSTS.Common.Severity", "value": "2 - High" }
]
```

---

## Repository Operations

### MCP Tools

- `mcp__azure-devops__list_repositories` - List all repos
- `mcp__azure-devops__get_repository` - Repo details
- `mcp__azure-devops__get_file_content` - Read file from repo

### Azure CLI Commands

```bash
# List repositories
az repos list \
  --org https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  -o table

# Get file content
az repos show \
  --org https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  --repository {REPO_NAME}
```

---

## Repository Reference

| Repository | Default Branch | AppRoleName | Team |
|------------|----------------|-------------|------|
| data-exchange-service | master | DataExchangeGateway | Alpha, Kilo |
| cortex-datamanagement-services | master | AppSupportService, DataPreparationService | Gamma |
| engagement-service | master | EngagementService | Alpha, Skyrockets |
| security-service | master | SecurityService | Skyrockets |
| data-kitchen-service | master | DataKitchenService, data-kitchen-function | Beta, Megatron |
| analytic-template-service | master | AnalyticTemplateService, AnalyticTemplateFunction | Tera |
| notification-service | master | NotificationService, Notification-UI-MFE | Beta, Skyrockets |
| staging-service | master | StagingService, staging-*-function | Gamma, Alpha |
| spark-job-management | master | SparkJobManagementService, SparkJobManagementFunction | Alpha, Beta |
| cortex-ui | master | Cortex-UI | Tera |
| client-service | master | ClientService | Beta |
| workpaper-service | master | WorkpaperService, WorkpaperFunction | Giga |
| async-workflow-framework | master | async-workflow-function | Alpha, Giga |
| sampling-service | master | SamplingService | Giga |
| localization-service | master | LocalizationService | Justice League, Skyrockets |
| scheduler-service | master | SchedulerService | Alpha |
| cortexpy | master | cortexpy | Delta, Beta |
| analytic-notebooks | master | analytic-notebooks | Beta |

### Clone URL Pattern

```bash
git clone git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/{REPO_NAME} ~/code/{REPO_NAME}
```

---

## Best Practices

1. **Use REST API for HTML fields** - az CLI has shell escaping issues with complex HTML
2. **Always specify organization and project** - Use full org URL
3. **Use WIQL for complex queries** - More flexible than field filtering
4. **Check field names** - Use `az boards work-item show` to discover available fields
5. **Handle relations separately** - Add parent/child links after work item creation
