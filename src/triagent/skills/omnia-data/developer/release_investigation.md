---
name: release_investigation
display_name: "Release Investigation"
description: "Investigate release pipeline failures and build issues"
version: "1.0.0"
tags: [pipelines, release, builds, investigation]
requires: [ado_basics]
subagents: []
tools:
  - mcp__azure-devops__list_pipelines
  - mcp__azure-devops__get_pipeline
  - mcp__azure-devops__list_pipeline_runs
  - mcp__azure-devops__get_pipeline_run
  - mcp__azure-devops__pipeline_timeline
  - mcp__azure-devops__get_pipeline_log
triggers:
  - "pipeline.*fail"
  - "build.*fail"
  - "release.*issue"
  - "deploy.*error"
---

## Release Pipeline Investigation

### Investigation Workflow

1. **Identify Pipeline**: Use `mcp__azure-devops__list_pipelines` to find the pipeline
2. **Get Recent Runs**: Use `mcp__azure-devops__list_pipeline_runs` for history
3. **Analyze Run**: Use `mcp__azure-devops__get_pipeline_run` for details
4. **View Timeline**: Use `mcp__azure-devops__pipeline_timeline` for stage breakdown
5. **Read Logs**: Use `mcp__azure-devops__get_pipeline_log` for error details

### Common Failure Patterns

| Pattern | Typical Cause | Investigation |
|---------|--------------|---------------|
| Timeout | Long-running tests, slow dependencies | Check timeline for slow stages |
| Agent offline | Pool capacity, maintenance | Check agent status |
| Test failure | Code regression, flaky tests | Read test output logs |
| Deployment error | Environment config, permissions | Check deployment logs |
| Build error | Compilation issues, missing deps | Read build logs |

### Investigation Questions

When investigating failures:
1. When did the failure start? (identify first failing build)
2. What changed? (commits between last success and failure)
3. Is it intermittent or consistent?
4. Does it fail in all environments or specific ones?

### Reporting Findings

After investigation, provide:
- Root cause analysis
- Affected builds/releases
- Remediation steps
- Prevention recommendations
