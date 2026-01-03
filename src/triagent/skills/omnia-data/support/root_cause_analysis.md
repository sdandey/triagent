---
name: root_cause_analysis
display_name: "Root Cause Analysis"
description: "Structured RCA process for production incidents"
version: "1.0.0"
tags: [rca, incident, support, investigation]
requires: [telemetry_basics, ado_basics]
subagents: [rca-analyzer]
tools:
  - mcp__triagent__generate_kusto_query
  - mcp__azure-devops__create_work_item
  - mcp__azure-devops__update_work_item
triggers:
  - "rca"
  - "root cause"
  - "incident.*analysis"
  - "postmortem"
---

## Root Cause Analysis Process

### RCA Framework

Follow the 5 Whys methodology to find the true root cause:

1. **What happened?** - Describe the incident impact
2. **Why did it happen?** - Technical cause
3. **Why wasn't it caught?** - Detection gap
4. **Why wasn't it prevented?** - Prevention gap
5. **What will prevent recurrence?** - Action items

### Investigation Steps

1. **Timeline Construction**
   - When did the issue start?
   - When was it detected?
   - When was it resolved?
   - Key events in between

2. **Impact Assessment**
   - Services affected
   - Users/requests impacted
   - Data integrity issues
   - SLA breaches

3. **Root Cause Identification**
   - Direct cause (what failed)
   - Contributing factors
   - Process/system gaps

### RCA Document Template

```markdown
## Incident Summary
[Brief description of what happened]

## Timeline
| Time | Event |
|------|-------|
| HH:MM | First symptom |
| HH:MM | Detection |
| HH:MM | Resolution |

## Impact
- Services: [list]
- Users affected: [count]
- Duration: [time]

## Root Cause
[Technical explanation]

## Contributing Factors
1. [Factor 1]
2. [Factor 2]

## Action Items
| Action | Owner | Due Date |
|--------|-------|----------|
| [Action] | [Name] | [Date] |
```

### Best Practices

1. Focus on systems, not blame
2. Include both immediate and long-term fixes
3. Track action items to completion
4. Share learnings with the team
