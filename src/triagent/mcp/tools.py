"""In-process MCP server with triagent-specific tools.

This module provides custom tools for triagent using the Claude Agent SDK's
@tool decorator and create_sdk_mcp_server() function.
"""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool


@tool("get_team_config", "Get triagent team configuration", {"team": str})
async def get_team_config_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Get team configuration for Kusto queries and ADO context.

    Args:
        args: Dict with 'team' key for team name

    Returns:
        Tool result with team configuration or error
    """
    from triagent.teams.config import get_team_config

    team = args.get("team", "omnia-data")
    config = get_team_config(team)

    if config:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""Team Configuration:
- Display Name: {config.display_name}
- ADO Organization: {config.ado_organization}
- ADO Project: {config.ado_project}""",
                }
            ]
        }
    return {
        "content": [{"type": "text", "text": f"Team '{team}' not found"}],
        "is_error": True,
    }


@tool(
    "generate_kusto_query",
    "Generate a Kusto query template for Azure Application Insights",
    {
        "type": "object",
        "properties": {
            "table": {
                "type": "string",
                "description": "Table: AppExceptions, AppRequests, AppDependencies, AppTraces",
            },
            "timespan": {
                "type": "string",
                "description": "Time range (e.g., '1h', '24h', '7d')",
            },
            "filter": {
                "type": "string",
                "description": "Optional filter expression",
            },
        },
        "required": ["table"],
    },
)
async def generate_kusto_query_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Generate Kusto query templates for triagent investigations.

    Args:
        args: Dict with 'table', optional 'timespan' and 'filter'

    Returns:
        Tool result with generated Kusto query
    """
    table = args.get("table", "AppExceptions")
    timespan = args.get("timespan", "24h")
    filter_expr = args.get("filter", "")

    # Build query
    query_parts = [
        table,
        f"| where timestamp > ago({timespan})",
    ]

    if filter_expr:
        query_parts.append(f"| where {filter_expr}")

    query_parts.extend(
        [
            "| order by timestamp desc",
            "| take 100",
        ]
    )

    query = "\n".join(query_parts)

    return {"content": [{"type": "text", "text": query}]}


@tool(
    "list_telemetry_tables",
    "List available Application Insights telemetry tables",
    {},
)
async def list_telemetry_tables_tool(args: dict[str, Any]) -> dict[str, Any]:
    """List available Application Insights telemetry tables.

    Returns:
        Tool result with table descriptions
    """
    tables = """Available Application Insights Tables:

1. **AppExceptions** - Application exceptions and stack traces
   - Fields: timestamp, problemId, outerMessage, innermostMessage, details

2. **AppRequests** - HTTP requests and responses
   - Fields: timestamp, name, url, resultCode, duration, success

3. **AppDependencies** - External dependency calls (SQL, HTTP, etc.)
   - Fields: timestamp, name, target, type, duration, success

4. **AppTraces** - Application log messages
   - Fields: timestamp, message, severityLevel, customDimensions

5. **AppPerformanceCounters** - Performance metrics
   - Fields: timestamp, name, value, category

6. **AppEvents** - Custom events
   - Fields: timestamp, name, customDimensions, customMeasurements"""

    return {"content": [{"type": "text", "text": tables}]}


def create_triagent_mcp_server():
    """Create in-process MCP server with triagent tools.

    Returns:
        McpSdkServerConfig for use with ClaudeAgentOptions.mcp_servers
    """
    return create_sdk_mcp_server(
        name="triagent",
        version="0.1.0",
        tools=[
            get_team_config_tool,
            generate_kusto_query_tool,
            list_telemetry_tables_tool,
        ],
    )
