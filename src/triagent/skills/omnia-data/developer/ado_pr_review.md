---
name: ado_pr_review
display_name: "ADO PR Review"
description: "Manage pull request reviews with inline comments and vote management"
version: "1.0.0"
tags: [ado, pull-request, code-review]
requires: [ado_basics]
subagents: []
tools:
  - mcp__azure-devops__list_pull_requests
  - mcp__azure-devops__get_pull_request_changes
  - mcp__azure-devops__get_pull_request_comments
  - mcp__azure-devops__get_pull_request_checks
  - mcp__azure-devops__add_pull_request_comment
  - mcp__azure-devops__update_pull_request
triggers:
  - "pr.*review"
  - "pull request"
  - "review pr"
---

## Pull Request Review Workflow

### Review Process

1. **List PRs**: Use `mcp__azure-devops__list_pull_requests` to find active PRs
2. **Get Changes**: Use `mcp__azure-devops__get_pull_request_changes` to see files modified
3. **Check Status**: Use `mcp__azure-devops__get_pull_request_checks` for CI status
4. **Read Comments**: Use `mcp__azure-devops__get_pull_request_comments` for context

### Adding Inline Comments

When posting review comments:

- Use `mcp__azure-devops__add_pull_request_comment` for inline feedback
- Specify file path and line numbers for precise placement
- Include severity: info, suggestion, warning, or issue
- Provide actionable feedback with code examples when possible

### Comment Format

Structure comments clearly:
- **Issue**: Describe the problem
- **Impact**: Explain why it matters
- **Suggestion**: Provide a fix or alternative

### Voting

After review, set appropriate vote:
- **Approved**: Code meets standards
- **Approved with suggestions**: Minor improvements recommended
- **Wait for author**: Changes required before merge
- **Rejected**: Significant issues that block merge
