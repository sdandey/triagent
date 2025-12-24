"""Defect/Incident Investigation Subagent.

This subagent investigates Azure DevOps defects and incidents by:
1. Gathering work item details from Azure DevOps
2. Asking the user for microservice/component context
3. Reading telemetry configuration from team memory files
4. Generating Kusto queries for Log Analytics investigation
"""

from __future__ import annotations

DEFECT_INVESTIGATOR_PROMPT = """
You are an expert defect investigator for Azure DevOps work items.

## Your Workflow:

### 1. Gather Defect Details
Use Azure DevOps MCP tools to fetch work item details:
- Work item ID, title, description, priority, state
- Assigned to, created date, related items
- Comments and discussion history

### 2. Identify Investigation Scope
Ask the user to specify:
- Which microservice or component is affected?
- What is the timeframe of the issue?
- Are there specific error messages or patterns to look for?
- Which environment (DEV, QAS, STG, PRD)?

### 3. Read Telemetry Configuration
Read the team's memory file (`omnia_data.md`) to get:
- Log Analytics Workspace name for the environment
- Relevant tables (AppExceptions, AppTraces, AppRequests, AppDependencies)
- Service names (CloudRoleName/AppRoleName) for the affected microservice

### 4. Generate Kusto Queries
Based on the defect details and telemetry config, generate queries for:
- Exception search matching error patterns
- Failed requests in the timeframe
- Dependency failures (SQL, HTTP, Service Bus)
- Trace log correlation

### 5. Present Findings
Summarize:
- Key error patterns to investigate
- Suggested Kusto queries to run in Azure Portal
- Related work items or PRs if found
- Recommended next steps

## Available Tools:
- Azure DevOps MCP tools (wit_get_work_item, wit_list_work_item_comments)
- Azure CLI (az boards work-item show)
- Read (for memory files and code)
- Glob/Grep (for searching codebase)
- AskUserQuestion (for clarification)

## Log Analytics Workspaces by Region:

### AME (Americas)
| Type | Workspace | Use For |
|------|-----------|---------|
| Non-Prod | npdamecortexlaw | DEV, DEV1, DEV2, QAS, QAS1, QAS2, LOD |
| Prod | prdamecortexlaw | STG, STG2, CNT1, PRD |
| BCP | bcpamecortexlaw | BCP |

### EMA (Europe/Middle East/Africa)
| Type | Workspace | Use For |
|------|-----------|---------|
| Non-Prod | npdemacortexlaw | INT, STG |
| Prod | prdemacortexlaw | PRD |
| BCP | bcpemacortexlaw | BCP |

### APAC (Asia Pacific)
| Type | Workspace | Use For |
|------|-----------|---------|
| Prod | prdapacortexlaw | STG, PRD |
| BCP | bcpapacortexlaw | BCP |

## Kusto Query Templates:

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

### Spark Job Management Specific
```kusto
AppTraces
| where TimeGenerated > ago(24h)
| where AppRoleName == "SparkJobManagementService"
| where Message contains "{job_id}" or Message contains "{error_pattern}"
| project TimeGenerated, Message, SeverityLevel
| order by TimeGenerated desc
```

## Important Notes:
- Always ask for clarification before running broad queries
- Use timeframe from defect creation date if not specified
- Look for related work items and PRs
- Suggest specific next steps based on findings
- Include the Azure Portal URL for running queries
"""

DEFECT_INVESTIGATOR_CONFIG = {
    "name": "defect-investigator",
    "description": "Investigate Defects and Incidents by gathering context from Azure DevOps and generating Kusto queries for telemetry analysis",
    "prompt": DEFECT_INVESTIGATOR_PROMPT,
    "tools": [
        "mcp__azure-devops__wit_get_work_item",
        "mcp__azure-devops__wit_list_work_item_comments",
        "mcp__azure-devops__search_workitem",
        "Read",
        "Glob",
        "Grep",
        "Bash",
    ],
    "model": "sonnet",
}


def get_workspace_for_environment(region: str, environment: str) -> str:
    """Get the Log Analytics workspace name for a given region and environment.

    Args:
        region: Region code (AME, EMA, APAC)
        environment: Environment name (DEV, QAS, STG, PRD, BCP, etc.)

    Returns:
        Log Analytics workspace name
    """
    region = region.upper()
    environment = environment.upper()

    # AME workspaces
    if region == "AME":
        if environment in ("DEV", "DEV1", "DEV2", "QAS", "QAS1", "QAS2", "LOD"):
            return "npdamecortexlaw"
        elif environment in ("STG", "STG2", "CNT1", "PRD"):
            return "prdamecortexlaw"
        elif environment == "BCP":
            return "bcpamecortexlaw"

    # EMA workspaces
    elif region == "EMA":
        if environment in ("INT", "STG"):
            return "npdemacortexlaw"
        elif environment == "PRD":
            return "prdemacortexlaw"
        elif environment == "BCP":
            return "bcpemacortexlaw"

    # APAC workspaces
    elif region == "APAC" or region == "APA":
        if environment in ("STG", "PRD"):
            return "prdapacortexlaw"
        elif environment == "BCP":
            return "bcpapacortexlaw"

    # Default to AME prod
    return "prdamecortexlaw"


def generate_exception_query(
    service_name: str,
    start_time: str,
    end_time: str,
    error_pattern: str | None = None,
) -> str:
    """Generate a Kusto query for exception search.

    Args:
        service_name: CloudRoleName/AppRoleName of the service
        start_time: Start time in ISO format
        end_time: End time in ISO format
        error_pattern: Optional error pattern to search for

    Returns:
        Kusto query string
    """
    query = f"""AppExceptions
| where TimeGenerated between (datetime({start_time}) .. datetime({end_time}))
| where AppRoleName == "{service_name}"
"""

    if error_pattern:
        query += f"""| where ProblemId contains "{error_pattern}" or OuterMessage contains "{error_pattern}"
"""

    query += """| summarize Count=count() by ProblemId, OuterMessage, AppRoleName
| top 20 by Count"""

    return query


def generate_request_failure_query(
    service_name: str,
    start_time: str,
    end_time: str,
) -> str:
    """Generate a Kusto query for request failures.

    Args:
        service_name: CloudRoleName/AppRoleName of the service
        start_time: Start time in ISO format
        end_time: End time in ISO format

    Returns:
        Kusto query string
    """
    return f"""AppRequests
| where TimeGenerated between (datetime({start_time}) .. datetime({end_time}))
| where AppRoleName == "{service_name}"
| where Success == false
| summarize Count=count() by Name, ResultCode, AppRoleName
| top 20 by Count"""


def generate_dependency_failure_query(
    service_name: str,
    start_time: str,
    end_time: str,
) -> str:
    """Generate a Kusto query for dependency failures.

    Args:
        service_name: CloudRoleName/AppRoleName of the service
        start_time: Start time in ISO format
        end_time: End time in ISO format

    Returns:
        Kusto query string
    """
    return f"""AppDependencies
| where TimeGenerated between (datetime({start_time}) .. datetime({end_time}))
| where AppRoleName == "{service_name}"
| where Success == false
| summarize Count=count() by Name, Target, ResultCode, DependencyType
| top 20 by Count"""


def generate_trace_search_query(
    service_name: str,
    start_time: str,
    end_time: str,
    search_term: str,
) -> str:
    """Generate a Kusto query for trace log search.

    Args:
        service_name: CloudRoleName/AppRoleName of the service
        start_time: Start time in ISO format
        end_time: End time in ISO format
        search_term: Term to search for in messages

    Returns:
        Kusto query string
    """
    return f"""AppTraces
| where TimeGenerated between (datetime({start_time}) .. datetime({end_time}))
| where AppRoleName == "{service_name}"
| where Message contains "{search_term}"
| project TimeGenerated, Message, SeverityLevel, AppRoleName
| top 100 by TimeGenerated desc"""
