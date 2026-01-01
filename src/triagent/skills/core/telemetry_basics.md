---
name: telemetry_basics
display_name: "Telemetry Basics"
description: "Core telemetry concepts and Azure Log Analytics fundamentals"
version: "1.0.0"
tags: [telemetry, kusto, log-analytics, core]
requires: []
subagents: []
tools:
  - mcp__triagent__generate_kusto_query
  - mcp__triagent__list_telemetry_tables
triggers: []
---

## Telemetry Fundamentals

You have access to telemetry tools for querying Azure Log Analytics.

### Available Tables

Key telemetry tables in the Audit Cortex environment:

| Table | Purpose |
|-------|---------|
| AppExceptions | Application exceptions and errors |
| AppTraces | Application log traces |
| AppRequests | HTTP request telemetry |
| AppDependencies | External dependency calls |
| AppMetrics | Custom and built-in metrics |

### Kusto Query Basics

Use `mcp__triagent__generate_kusto_query` to help build Kusto queries. Common patterns:

```kusto
// Filter by time range
| where TimeGenerated > ago(24h)

// Filter by environment
| where AppRoleName == "ServiceName"

// Count by type
| summarize count() by ExceptionType
```

### Best Practices

1. Always include a time filter to limit query scope
2. Use `project` to select only needed columns
3. Aggregate with `summarize` for large datasets
4. Filter early in the query pipeline for performance
