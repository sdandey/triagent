---
name: lsi_creation
display_name: "LSI Creation"
description: "Create and manage Live Site Incidents (LSI) for production issues"
version: "1.0.0"
tags: [lsi, incident, production, support]
requires: [ado_basics, telemetry_basics]
subagents: []
tools:
  - mcp__azure-devops__create_work_item
  - mcp__azure-devops__update_work_item
  - mcp__azure-devops__manage_work_item_link
triggers:
  - "create.*lsi"
  - "live site"
  - "production.*incident"
  - "outage"
---

## Live Site Incident (LSI) Management

### When to Create an LSI

Create an LSI when:
- Production service is degraded or unavailable
- Critical functionality is broken
- Data integrity issues are discovered
- Security incidents occur
- SLA breaches happen

### LSI Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| Title | "LSI: [Service] - [Issue]" | "LSI: EngagementService - API Timeouts" |
| Type | Bug or appropriate work item type | Bug |
| Severity | 1-Critical, 2-High, 3-Medium | 1 - Critical |
| Priority | 1-Critical, 2-High, 3-Medium, 4-Low | 1 |
| Area Path | Team area | Audit Cortex 2\Omnia Data |
| Tags | "LSI", environment, service | "LSI, PRD, EngagementService" |

### LSI Description Template

```markdown
## Incident Summary
[Brief description of the production issue]

## Detection
- **Time Detected**: [Timestamp UTC]
- **Detection Method**: [Monitoring alert / User report / etc.]
- **Reporter**: [Name/Team]

## Impact Assessment
- **Severity**: [1-Critical / 2-High / 3-Medium / 4-Low]
- **Affected Services**: [List of services]
- **Affected Environments**: [PRD / STG / etc.]
- **User Impact**: [Description of user-facing impact]
- **Estimated Users Affected**: [Number or percentage]

## Current Status
- **Status**: [Investigating / Mitigating / Resolved]
- **Assigned To**: [On-call engineer / Team]

## Timeline
| Time (UTC) | Event |
|------------|-------|
| [Time] | Issue detected |
| [Time] | Investigation started |
| [Time] | Root cause identified |
| [Time] | Mitigation applied |
| [Time] | Issue resolved |

## Technical Details
[Include relevant error messages, stack traces, or telemetry data]

## Mitigation Steps
1. [Step taken to mitigate]
2. [Additional steps]

## Root Cause (if known)
[Brief explanation, full RCA to follow]

## Action Items
- [ ] [Post-incident action]
- [ ] [Create RCA document]
- [ ] [Update monitoring/alerts]
```

### LSI Workflow

1. **Create LSI** immediately upon production issue detection
2. **Update Status** as investigation progresses
3. **Link Related Items** (defects, deployments, etc.)
4. **Document Timeline** with key events
5. **Close LSI** after issue is resolved
6. **Create RCA** work item linked to LSI
