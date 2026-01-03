---
name: lsi_creation
display_name: "LSI Creation"
description: "Create and manage Live Site Incidents (LSI) for production issues"
version: "1.1.0"
tags: [lsi, incident, production, support]
requires: [ado_basics, telemetry_basics, ado_lsi_defect]
subagents: [ado-work-item-manager]
tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - "create.*lsi"
  - "live site"
  - "production.*incident"
  - "outage"
---

## Live Site Incident (LSI) Management

> **Note**: This skill extends the `ado_lsi_defect` core skill with LSI-specific workflows.
> Refer to `ado_lsi_defect` for detailed field mappings, HTML templates, and REST API workflows.

### When to Create an LSI

Create an LSI when:
- Production service is degraded or unavailable
- Critical functionality is broken
- Data integrity issues are discovered
- Security incidents occur
- SLA breaches happen

### LSI-Specific Title Format

```
[REGION ENV] Service | LSI: Issue Summary
```

Examples:
- `[AME PRD] WorkpaperService | LSI: OutOfMemoryException during purge`
- `[EMA PRD] EngagementService | LSI: API Timeouts exceeding 30s`

### LSI Required Fields

See `ado_lsi_defect` core skill for complete field reference. Key LSI-specific fields:

| Field | Value |
|-------|-------|
| **Severity** | Usually `1 - Critical` or `2 - High` |
| **Parent Epic** | 5150584 (Live Site Incidents \| 2025) |
| **Tags** | Include "LSI" tag |

### LSI Workflow

1. **Create LSI** immediately upon production issue detection
   - Use `ado_lsi_defect` skill for work item creation
   - Always link to Live Site Incidents Epic (5150584)

2. **Update Status** as investigation progresses
   - Add timeline comments
   - Update Description with findings

3. **Link Related Items**
   - Defects created for fixes
   - Related deployments
   - RCA documents

4. **Document Timeline** with key events
   - Detection time
   - Investigation milestones
   - Resolution time

5. **Close LSI** after issue is resolved
   - Update state to Resolved/Closed
   - Ensure all acceptance criteria met

6. **Create RCA** work item linked to LSI
   - Link as Related work item

### Quick LSI Creation Command

When user says "create LSI for {service}", follow this workflow:

1. Gather telemetry data for the service
2. Prompt for missing required fields (see `ado_lsi_defect`)
3. Auto-populate team fields based on service
4. Create work item with HTML formatting
5. Link to LSI Epic (5150584)
6. Display created work item details
