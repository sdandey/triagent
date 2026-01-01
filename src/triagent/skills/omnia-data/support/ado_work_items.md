---
name: ado_work_items
display_name: "ADO Work Items"
description: "Create and manage defects, incidents, and work items in Azure DevOps"
version: "1.0.0"
tags: [ado, work-items, defects, incidents, support]
requires: [ado_basics]
subagents: [work-item-manager]
tools:
  - mcp__azure-devops__create_work_item
  - mcp__azure-devops__update_work_item
  - mcp__azure-devops__get_work_item
  - mcp__azure-devops__search_work_items
  - mcp__azure-devops__manage_work_item_link
triggers:
  - "create.*defect"
  - "create.*bug"
  - "create.*incident"
  - "update.*work item"
  - "link.*work item"
---

## Work Item Management

### Creating Work Items

When creating work items, gather required information:

| Field | Description | Required |
|-------|-------------|----------|
| Title | Clear, descriptive summary | Yes |
| Work Item Type | Bug, Task, User Story, etc. | Yes |
| Description | Detailed explanation | Yes |
| Area Path | Team/component area | Recommended |
| Assigned To | Owner | Recommended |
| Priority | 1 (Critical) to 4 (Low) | Recommended |
| Tags | Categorization labels | Optional |

### Defect Template

When creating defects, include:

```markdown
## Environment
[PRD/STG/QAS/DEV]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Impact
[User/business impact]

## Workaround
[If any exists]

## Related Items
[Links to incidents, LSIs, etc.]
```

### Incident Template

For production incidents:

```markdown
## Incident Summary
[Brief description]

## Severity
[Critical/High/Medium/Low]

## Impact
- Services affected: [list]
- Users impacted: [count/scope]
- Start time: [timestamp]
- Resolution time: [timestamp]

## Resolution
[How it was fixed]

## Root Cause
[Brief explanation, link to full RCA]
```

### Linking Work Items

Use `mcp__azure-devops__manage_work_item_link` to:
- Link related defects
- Connect to parent/child items
- Associate with incidents
- Reference documentation
