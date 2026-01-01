---
name: telemetry_investigation
display_name: "Telemetry Investigation"
description: "Investigate production issues using Azure Log Analytics telemetry"
version: "1.0.0"
tags: [telemetry, investigation, kusto, support]
requires: [telemetry_basics]
subagents: [kusto-query-builder]
tools:
  - mcp__triagent__generate_kusto_query
  - mcp__triagent__list_telemetry_tables
triggers:
  - "investigate.*exception"
  - "check.*logs"
  - "query.*telemetry"
  - "find.*error"
---

## Telemetry Investigation Guide

### Investigation Workflow

1. **Gather Context**
   - Environment (PRD, STG, QAS, DEV)
   - Time range of issue
   - Affected service/AppRoleName
   - Error symptoms or user reports

2. **Query Exceptions**
   ```kusto
   AppExceptions
   | where TimeGenerated > ago(24h)
   | where AppRoleName == "ServiceName"
   | summarize count() by ExceptionType, ProblemId
   | order by count_ desc
   ```

3. **Analyze Patterns**
   - Exception frequency over time
   - Correlation with deployments
   - Impact on request success rates
   - User/client distribution

### Common Investigation Queries

| Investigation | Query Focus |
|--------------|-------------|
| Error spike | Count exceptions by time bucket |
| New errors | Exceptions not seen before timeframe |
| Affected users | Distinct users with errors |
| Root cause | Exception stack traces with dedup |
| Service health | Request success/failure rates |

### Best Practices

1. Always start with a time-bounded query
2. Use summarize to understand patterns before deep diving
3. Correlate exceptions with requests using operation_Id
4. Check for recent deployments as potential causes
5. Document findings with timestamps and query links
