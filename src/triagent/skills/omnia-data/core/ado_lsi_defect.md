---
name: ado_lsi_defect
display_name: "ADO LSI/Defect Creation"
description: "Create Live Site Incident defects with automated field population and HTML formatting"
version: "1.0.0"
tags: [ado, lsi, defect, incident, core, work-item]
requires: [ado_basics]
subagents: [ado-work-item-manager]
tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - "create.*lsi"
  - "create.*defect"
  - "live site.*incident"
  - "production.*issue"
  - "create.*work.*item"
---

# ADO LSI/Defect Creation Guide

This skill provides comprehensive guidance for creating Live Site Incident (LSI) defects in Azure DevOps with proper field population, team routing, and HTML formatting.

---

## Required Fields Checklist

Before creating an LSI/Defect, gather the following required information. **Use AskUserQuestion tool to prompt for any missing fields.**

### Mandatory Fields (Must Prompt if Missing)

| Field | ADO Path | Options/Format | Required |
|-------|----------|----------------|----------|
| **Title** | `System.Title` | `[REGION ENV] Service \| Issue Summary` | Yes |
| **Severity** | `Microsoft.VSTS.Common.Severity` | `1 - Critical`, `2 - High`, `3 - Medium`, `4 - Low` | Yes |
| **Found in Release** | `Custom.FoundinCortexRelease#` | `9.5`, `9.4`, etc. | Yes |
| **Target Release** | `Custom.CortexRelease#` | `9.6`, `9.5.1`, etc. | Yes |
| **Environment** | `Custom.CortexEnvironment` | `PRD`, `STG`, `QAS`, `DEV` | Yes |
| **Service/AppRoleName** | (for team detection) | e.g., `WorkpaperService` | Yes |

### Auto-Populated Fields (No Prompt Needed)

| Field | ADO Path | Auto-Population Logic |
|-------|----------|----------------------|
| **Area Path** | `System.AreaPath` | Derived from Service → Team mapping |
| **Iteration Path** | `System.IterationPath` | Current Program Increment |
| **Scrum Team** | `Custom.ScrumTeam` | From service mapping |
| **POD Team** | `Custom.PodTeam` | From service mapping |
| **Priority** | `Microsoft.VSTS.Common.Priority` | Default: 2 |
| **Work Item Type** | `System.WorkItemType` | Fixed: "Defect" |

### Optional Fields (Prompt if Relevant)

| Field | ADO Path | When to Include |
|-------|----------|-----------------|
| **Parent Epic** | Parent link | Link to "Live Site Incidents \| 2025" Epic (5150584) |
| **Assigned To** | `System.AssignedTo` | If known |
| **Root Cause Category** | `Custom.CortexRootCauseCategory` | `Code Issue`, `Other Issue`, `Configuration Issue` |

---

## Service to Team Mapping

Use this mapping to auto-populate Area Path, Scrum Team, and POD Team based on the affected service.

### Omnia Data Services

| CloudRoleName | Team | POD | Area Path Suffix |
|---------------|------|-----|------------------|
| `WorkpaperService`, `WorkpaperFunction` | Giga | Data in Use | `Data In Use\Giga` |
| `EngagementService`, `EngagementServiceFunction` | Alpha | Data Acquisition and Preparation | `Data Acquisition and Preparation\Alpha` |
| `DataKitchenService`, `data-kitchen-function` | Beta | Data Acquisition and Preparation | `Data Acquisition and Preparation\Beta` |
| `StagingService`, `staging-*-function` | Gamma | Data Management and Activation | `Data Management and Activation\Gamma` |
| `SecurityService` | Skyrockets | Data Management and Activation | `Data Management and Activation\Skyrockets` |
| `DataPreparationService`, `DataPreparationFunction` | Gamma | Data Management and Activation | `Data Management and Activation\Gamma` |
| `NotificationService`, `Notification-UI-MFE` | Beta | Data Acquisition and Preparation | `Data Acquisition and Preparation\Beta` |
| `SparkJobManagementService`, `SparkJobManagementFunction` | Alpha | Data Acquisition and Preparation | `Data Acquisition and Preparation\Alpha` |
| `SchedulerService` | Alpha | Data Acquisition and Preparation | `Data Acquisition and Preparation\Alpha` |
| `ClientService` | Beta | Data Acquisition and Preparation | `Data Acquisition and Preparation\Beta` |
| `SamplingService` | Giga | Data in Use | `Data In Use\Giga` |
| `AnalyticTemplateService`, `AnalyticTemplateFunction` | Tera | Data in Use | `Data In Use\Tera` |
| `DataExchangeGateway`, `DataExchangeGatewayFunction` | Alpha | Data Acquisition and Preparation | `Data Acquisition and Preparation\Alpha` |
| `LocalizationService` | Justice League | Omnia JE | `Omnia JE\Justice League` |
| `async-workflow-function` | Giga | Data in Use | `Data In Use\Giga` |

### Area Path Construction

```
Audit Cortex 2\Omnia Data\Omnia Data Automation\{Area Path Suffix}
```

Example: `WorkpaperService` → `Audit Cortex 2\Omnia Data\Omnia Data Automation\Data In Use\Giga`

### Current Iteration Path

```
Audit Cortex 2\Program Increment 22
```

---

## HTML Field Templates

Use clean HTML format for all rich-text fields. Always use the REST API approach with JSON payload for proper HTML rendering.

### Description Template

```html
<div style="font-family: Segoe UI, sans-serif;">
  <h2 style="color: #d13438; border-bottom: 2px solid #d13438; padding-bottom: 5px;">
    Critical: {Issue Title}
  </h2>

  <h3>Issue Summary</h3>
  <p>{Brief description of the issue}</p>

  <h3>Exception Metrics (Last 30 Days)</h3>
  <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
    <thead style="background-color: #0078d4; color: white;">
      <tr>
        <th>Region</th>
        <th>Environment</th>
        <th>Service</th>
        <th>Exception Count</th>
        <th>First Seen</th>
        <th>Last Seen</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      <tr style="background-color: #fce4e4;">
        <td><b>AME</b></td>
        <td>PRD</td>
        <td>{ServiceName}</td>
        <td style="color: #d13438; font-weight: bold;">{count}</td>
        <td>{date}</td>
        <td>{date}</td>
        <td>Active</td>
      </tr>
      <!-- Add rows for EMA, APA as needed -->
    </tbody>
  </table>

  <h3>Root Cause Analysis</h3>
  <ol>
    <li><b>Issue 1:</b> {description}</li>
    <li><b>Issue 2:</b> {description}</li>
  </ol>

  <h3>Affected Code Files</h3>
  <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
    <thead style="background-color: #e1e1e1;">
      <tr><th>File</th><th>Line</th><th>Issue</th><th>Severity</th></tr>
    </thead>
    <tbody>
      <tr>
        <td><code>{file_path}</code></td>
        <td>{line}</td>
        <td>{issue description}</td>
        <td style="color: #d13438;">Critical</td>
      </tr>
    </tbody>
  </table>

  <h3>Recommended Fixes</h3>
  <ol>
    <li><b>Fix 1:</b> {description}</li>
    <li><b>Fix 2:</b> {description}</li>
  </ol>
</div>
```

### Acceptance Criteria Template

```html
<div>This defect is complete when:</div>
<div><br></div>
<ol>
  <li><b>Fix 1:</b> {specific acceptance criterion}</li>
  <li><b>Fix 2:</b> {specific acceptance criterion}</li>
  <li><b>Validation:</b> No exceptions observed in {ENV} for 7 consecutive days</li>
  <li><b>Unit Tests:</b> Tests added to validate the fix</li>
</ol>
```

### Root Cause Template

```html
<div>This was identified through telemetry analysis of {ENV} exceptions ({count} occurrences, {date range}).</div>
<div><br></div>
<div><b>Technical Root Cause:</b></div>
<ul>
  <li>{Root cause item 1 with code references}</li>
  <li>{Root cause item 2}</li>
</ul>
<div><br></div>
<div><b>Impact:</b></div>
<ul>
  <li>{Impact description}</li>
  <li>{Exception count} exceptions recorded in {ENV} over {time period}</li>
</ul>
```

### Repro Steps Template

```html
<div><b>Pre-requisites:</b></div>
<ul>
  <li>Access to {ENV} Log Analytics workspace ({workspace_id})</li>
  <li>{Other prerequisites}</li>
</ul>
<br/>
<div><b>Steps:</b></div>
<ol>
  <li>{Step 1}</li>
  <li>{Step 2}</li>
  <li>{Step 3}</li>
</ol>
<br/>
<div><b>Actual Result:</b> {exception or error}</div>
<div><b>Expected Result:</b> {correct behavior}</div>
```

### System Info Template

```html
<div><b>Environment:</b> {ENV}</div>
<div><b>Service:</b> {ServiceName}</div>
<div><b>Time Range:</b> {date range} ({count} occurrences)</div>
<div><b>Log Analytics Workspace:</b> {workspace_name} ({workspace_id})</div>
<br/>
<div><b>Kusto Query:</b></div>
<pre>
AppExceptions
| where TimeGenerated > ago(30d)
| where AppRoleName in ('{ServiceName}')
| where ProblemId contains '{ExceptionType}'
| summarize Count=count() by ProblemId
</pre>
```

---

## Work Item Creation Workflow

### Step 1: Gather Required Information

Use `AskUserQuestion` tool to prompt for any missing required fields:

```
Questions to ask if not provided:
1. Title: "What is the issue title? Format: [REGION ENV] Service | Issue Summary"
2. Severity: Options: "1 - Critical", "2 - High", "3 - Medium", "4 - Low"
3. Service: "Which service is affected?" (for team auto-detection)
4. Environment: Options: "PRD", "STG", "QAS", "DEV"
5. Found in Release: "Which release was this found in?" (e.g., "9.5")
6. Target Release: "Which release should this be fixed in?" (e.g., "9.6")
7. Parent Epic: "Should this be linked to Live Site Incidents Epic? (5150584)"
```

### Step 2: Auto-Populate Team Fields

Based on the service name, look up:
- Area Path from Service → Team mapping
- Scrum Team name
- POD Team name
- Iteration Path (current PI)

### Step 3: Create JSON Payload

Write a JSON file with PATCH operations:

```json
[
  { "op": "add", "path": "/fields/System.Title", "value": "{title}" },
  { "op": "add", "path": "/fields/System.AreaPath", "value": "{area_path}" },
  { "op": "add", "path": "/fields/System.IterationPath", "value": "Audit Cortex 2\\Program Increment 22" },
  { "op": "add", "path": "/fields/Microsoft.VSTS.Common.Severity", "value": "{severity}" },
  { "op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": 2 },
  { "op": "add", "path": "/fields/Custom.CortexRelease#", "value": "{target_release}" },
  { "op": "add", "path": "/fields/Custom.FoundinCortexRelease#", "value": "{found_in_release}" },
  { "op": "add", "path": "/fields/Custom.ScrumTeam", "value": "{scrum_team}" },
  { "op": "add", "path": "/fields/Custom.PodTeam", "value": "{pod_team}" },
  { "op": "add", "path": "/fields/Custom.CortexEnvironment", "value": "{environment}" },
  { "op": "add", "path": "/fields/System.Description", "value": "{html_description}" },
  { "op": "add", "path": "/fields/Microsoft.VSTS.TCM.ReproSteps", "value": "{html_repro_steps}" },
  { "op": "add", "path": "/fields/Microsoft.VSTS.TCM.SystemInfo", "value": "{html_system_info}" },
  { "op": "add", "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria", "value": "{html_acceptance}" },
  { "op": "add", "path": "/fields/Custom.CortexRootCause", "value": "{html_root_cause}" },
  { "op": "add", "path": "/fields/Custom.CortexRootCauseCategory", "value": "Code Issue" }
]
```

### Step 4: Create Work Item via REST API

```bash
# Get access token
PAT=$(az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv)

# Create work item
curl -s -X POST \
  "https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_apis/wit/workitems/\$Defect?api-version=7.0" \
  -H "Content-Type: application/json-patch+json" \
  -H "Authorization: Bearer $PAT" \
  -d @/tmp/create_workitem.json
```

### Step 5: Add Parent Link (Optional)

If parent Epic is specified:

```bash
curl -s -X PATCH \
  "https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_apis/wit/workitems/{work_item_id}?api-version=7.0" \
  -H "Content-Type: application/json-patch+json" \
  -H "Authorization: Bearer $PAT" \
  -d '[{"op": "add", "path": "/relations/-", "value": {"rel": "System.LinkTypes.Hierarchy-Reverse", "url": "https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_apis/wit/workItems/{parent_id}"}}]'
```

### Step 6: Display Created Work Item

After creation, display:
- Work Item ID
- Title
- Direct URL: `https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_workitems/edit/{id}`
- Key fields populated

---

## Common Parent Epics

| Epic ID | Title | Use Case |
|---------|-------|----------|
| 5150584 | Live Site Incidents \| 2025 | Production LSIs |
| (varies) | Sprint Epic | Sprint-specific work |

---

## Log Analytics Workspace Reference

| Region | Environment | Workspace ID |
|--------|-------------|--------------|
| AME | PRD, STG, CNT1 | `ed9e6912-0544-405b-921b-f2d6aad2155e` |
| AME | DEV, QAS | `874aa8fb-6d29-4521-920f-63ac7168404e` |
| EMA | PRD | `b3f751c4-5cce-4caa-a3fb-eccbe019c661` |
| APA | PRD | `d333bffc-5984-4bcd-a600-064988e7e2ec` |

---

## Quick Reference: Required Field Prompts

When creating an LSI/Defect, if any of these are missing, prompt the user:

```
AskUserQuestion prompts:

1. Title (if missing):
   Question: "What should be the work item title?"
   Header: "Title"
   Options: [User provides custom input]

2. Severity (if missing):
   Question: "What is the severity of this issue?"
   Header: "Severity"
   Options: ["1 - Critical", "2 - High", "3 - Medium", "4 - Low"]

3. Environment (if missing):
   Question: "Which environment is affected?"
   Header: "Environment"
   Options: ["PRD", "STG", "QAS", "DEV"]

4. Service (if cannot auto-detect):
   Question: "Which service is affected?"
   Header: "Service"
   Options: ["WorkpaperService", "EngagementService", "DataKitchenService", "Other"]

5. Target Release (if missing):
   Question: "Which release should this be fixed in?"
   Header: "Release"
   Options: ["9.6", "9.5.1", "9.5.2"]

6. Found in Release (if missing):
   Question: "Which release was this issue found in?"
   Header: "Found In"
   Options: ["9.5", "9.4", "9.3"]
```
