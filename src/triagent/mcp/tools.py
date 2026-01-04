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




# Language to skill name mapping for code review guidelines
LANGUAGE_SKILL_MAP = {
    "python": "python_code_review",
    "pyspark": "pyspark_code_review",
    "dotnet": "dotnet_code_review",
    "csharp": "dotnet_code_review",
}

# File extension to language mapping for auto-detection
EXTENSION_LANGUAGE_MAP = {
    ".py": "python",
    ".pyi": "python",
    ".ipynb": "pyspark",
    ".cs": "dotnet",
    ".csproj": "dotnet",
    ".sln": "dotnet",
}


@tool(
    "get_code_review_guidelines",
    "Get code review guidelines for a specific programming language. Use this before reviewing code.",
    {
        "type": "object",
        "properties": {
            "language": {
                "type": "string",
                "description": "Language: 'python', 'pyspark', 'dotnet', or 'auto' for auto-detection",
                "enum": ["python", "pyspark", "dotnet", "auto"],
            },
            "file_extensions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "File extensions for auto-detection when language is 'auto'",
            },
        },
        "required": ["language"],
    },
)
async def get_code_review_guidelines_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Get code review guidelines for a specific language.

    Call this tool before reviewing code to get the appropriate guidelines.

    Args:
        args: Dict with 'language' (python/pyspark/dotnet/auto) and optional 'file_extensions'

    Returns:
        Tool result with code review guidelines content
    """
    from triagent.skills.loader import load_skill_by_name

    language = args.get("language", "python")
    file_extensions = args.get("file_extensions", [])

    # Auto-detect language from file extensions
    if language == "auto":
        detected_languages: dict[str, int] = {}
        for ext in file_extensions:
            if ext.startswith("."):
                lang = EXTENSION_LANGUAGE_MAP.get(ext.lower())
            else:
                lang = EXTENSION_LANGUAGE_MAP.get(f".{ext.lower()}")
            if lang:
                detected_languages[lang] = detected_languages.get(lang, 0) + 1

        if detected_languages:
            # Use most common language
            language = max(detected_languages, key=detected_languages.get)
        else:
            language = "python"  # Default fallback

    # Get skill name for language
    skill_name = LANGUAGE_SKILL_MAP.get(language.lower(), "python_code_review")

    # Load skill content
    content = load_skill_by_name(skill_name)

    if content:
        text = "Code Review Guidelines for " + language.upper() + ":" + chr(10) + chr(10) + content
        return {
            "content": [
                {
                    "type": "text",
                    "text": text,
                }
            ]
        }

    return {
        "content": [
            {
                "type": "text",
                "text": f"No code review guidelines found for language: {language}"
            }
        ],
        "is_error": True,
    }

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
            get_code_review_guidelines_tool,
        ],
    )
