---
name: ado_basics
display_name: "Azure DevOps Basics"
description: "Core Azure DevOps navigation, work item access, and repository operations"
version: "1.0.0"
tags: [ado, core, work-items, repositories]
requires: []
subagents: []
tools:
  - mcp__azure-devops__get_work_item
  - mcp__azure-devops__list_work_items
  - mcp__azure-devops__search_work_items
  - mcp__azure-devops__list_repositories
  - mcp__azure-devops__get_repository
  - mcp__azure-devops__get_file_content
triggers: []
---

## Azure DevOps Core Operations

You have access to Azure DevOps MCP tools for work item and repository operations.

### Work Item Operations

- Use `mcp__azure-devops__get_work_item` to fetch details of a specific work item by ID
- Use `mcp__azure-devops__list_work_items` to list work items with optional filtering
- Use `mcp__azure-devops__search_work_items` for WIQL-based searches

### Repository Operations

- Use `mcp__azure-devops__list_repositories` to see all repositories in the project
- Use `mcp__azure-devops__get_repository` for details on a specific repo
- Use `mcp__azure-devops__get_file_content` to read file contents from a repository

### Best Practices

1. Always specify the project and organization from the team context
2. When searching work items, use WIQL for complex queries
3. For repository operations, prefer the repository name over ID when possible
