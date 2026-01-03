---
name: dotnet_code_review
display_name: ".NET Code Review"
description: "Review .NET/C# code changes in PRs with focus on patterns, performance, security"
version: "1.0.0"
tags: [code-review, dotnet, csharp]
requires: [ado_basics]
subagents: [csharp-code-reviewer]
tools:
  - mcp__azure-devops__get_pull_request_changes
  - mcp__azure-devops__add_pull_request_comment
  - Read
  - Glob
  - Grep
triggers:
  - "review.*\\.cs"
  - "review.*dotnet"
  - "review.*csharp"
---

## .NET Code Review Guidelines

When reviewing C#/.NET code, focus on:

### Architecture & Patterns

- SOLID principles adherence
- Dependency injection usage
- Repository and service layer separation
- Proper use of interfaces and abstractions

### Performance

- Async/await usage (avoid blocking calls)
- Efficient LINQ queries
- Memory allocations and object pooling
- Database query optimization

### Security

- Input validation and sanitization
- SQL injection prevention (parameterized queries)
- Secrets management (no hardcoded credentials)
- Authentication/authorization checks

### Best Practices

- Null reference handling (nullable reference types)
- Exception handling patterns
- Logging and observability
- Unit test coverage

### Review Process

1. Fetch PR changes using `mcp__azure-devops__get_pull_request_changes`
2. Analyze file extensions to confirm .NET files (.cs, .csproj)
3. Read file contents and review against guidelines
4. Post inline comments using `mcp__azure-devops__add_pull_request_comment`
5. Include severity (info, warning, issue) and suggested fixes
