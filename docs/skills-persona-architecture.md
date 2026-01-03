# Skills & Persona Architecture Design Document

**Document Version:** 1.1
**Prepared by:** Santosh Dandey
**Last Updated:** 2025-12-31 16:45:00
**Issue Reference:** [#10 - Add YAML frontmatter metadata to team CLAUDE.md files](https://github.com/sdandey/triagent/issues/10)
**Branch:** feature/skills-implementation

## Table of Contents

1. [Overview](#overview)
2. [User Requirements](#user-requirements)
3. [Architecture Design](#architecture-design)
4. [User Experience Flow](#user-experience-flow)
5. [Subagent Visibility](#subagent-visibility)
6. [Subagent Logging](#subagent-logging)
7. [Language Detection](#language-detection)
8. [File Structure](#file-structure)
9. [Data Models](#data-models)
10. [Implementation Phases](#implementation-phases)
11. [Acceptance Criteria](#acceptance-criteria)
12. [Document History](#document-history)

---

## Overview

This document describes the design for implementing a persona-based skill system for triagent. The system enables team-specific personas (Developer, Support) with composed skill sets, where each persona loads specialized subagents that are automatically invoked based on user requests.

### Goals

- Enable team-specific Developer and Support personas
- Provide automatic language detection for code review tasks
- Show visual indicators for which subagent is handling user requests
- Support Nerd Font icons with ASCII fallback for terminal compatibility

---

## User Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-1 | Team-specific Developer and Support personas (MVP: omnia-data only) | High |
| REQ-2 | File structure: `skills/{team-name}/{developer\|support}/skill-file.md` | High |
| REQ-3 | Core skills shared between personas (ADO, Telemetry) | High |
| REQ-4 | Selection flow: Team selection → Persona selection in /init | High |
| REQ-5 | Runtime switch via `/persona` command | Medium |
| REQ-6 | Each skill maps to subagents invoked via Task tool | High |
| REQ-7 | Subagent visibility with Nerd Font icons | Medium |
| REQ-8 | ASCII fallback for terminals without Nerd Fonts | Medium |
| REQ-9 | Auto language detection: "review PR #123" detects language from files | High |

### MVP Skills (omnia-data team)

| Developer Persona | Support Persona |
|-------------------|-----------------|
| .NET Code Review | Telemetry Investigation |
| Python Code Review | Root Cause Analysis |
| PySpark Code Review | ADO Work Items (defects, incidents, LSI) |
| ADO Inline PR Comments | Read/Update Work Items |
| Release Pipeline Investigation | All existing omnia_data.md features |
| ADO Work Item Creation | |

---

## Architecture Design

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Triagent CLI                            │
├─────────────────────────────────────────────────────────────────┤
│  /init Command                      /persona Command            │
│  ├─ Team Selection                  ├─ Show current persona     │
│  └─ Persona Selection               └─ Switch persona           │
├─────────────────────────────────────────────────────────────────┤
│                     TriagentSDKClient                           │
│  ├─ LoadedPersona                                               │
│  ├─ Subagent Definitions (AgentDefinition[])                    │
│  └─ Subagent Visibility Hooks                                   │
├─────────────────────────────────────────────────────────────────┤
│                      Skills System                              │
│  ├─ SkillLoader           ├─ SkillMetadata                      │
│  ├─ PersonaDefinition     ├─ SubagentConfig                     │
│  └─ LoadedPersona         └─ Language Detection                 │
├─────────────────────────────────────────────────────────────────┤
│                   Claude Agent SDK                              │
│  └─ ClaudeAgentOptions.agents: AgentDefinition[]                │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **TriagentConfig**: Extended with `persona` and `use_nerd_fonts` fields
2. **SkillLoader**: Parses YAML frontmatter from markdown files, loads personas
3. **LoadedPersona**: Runtime representation with resolved skills and subagents
4. **SubagentConfig**: Configuration for subagents passed to Claude SDK
5. **Subagent Visibility**: Hooks to display which subagent is handling requests

---

## User Experience Flow

### Persona Selection in /init

```
┌─────────────────────────────────────────────────────────────────┐
│  Welcome to Triagent CLI Setup                                  │
└─────────────────────────────────────────────────────────────────┘

Step 1/6: Claude API Provider
─────────────────────────────
✓ API provider configured: Azure AI Foundry

Step 2/6: Team Selection
─────────────────────────────
Select your team:
  1. Levvia
  2. Omnia
  3. Omnia Data (current)

Enter team number (1-3): 3
✓ Selected team: Omnia Data

Step 3/6: Persona Selection
─────────────────────────────
Select your persona:
  1. Developer - Code review, PR management, release investigation
  2. Support - Telemetry analysis, RCA, ADO work items

Enter persona number (1-2): 1
✓ Selected persona: Developer

Step 4/6: Azure DevOps MCP Server
...
```

### Runtime Persona Switch

```
triagent> /persona

Current persona: Developer
Available personas for omnia-data:
  1. Developer - Code review, PR management, release investigation (current)
  2. Support - Telemetry analysis, RCA, ADO work items

triagent> /persona support

Switching to Support persona...
✓ Persona changed to: Support
  Reloading skills and subagents...
```

---

## Subagent Visibility

When Claude invokes a subagent, the user sees a visual indicator with Nerd Font icons.

### User Experience

```
User: Review PR #123

┌─────────────────────────────────────────────────────────────────┐
│   Using C# Code Reviewer                                       │
│  Analyzing 8 files in data-kitchen-service...                   │
│                                                                 │
│  Reviewing: src/Services/DataProcessor.cs                       │
│  Reviewing: src/Controllers/KitchenController.cs                │
│  ...                                                            │
│                                                                 │
│  ✓ Review complete: 4 issues found                              │
│  Posting inline comments to PR #123...                          │
└─────────────────────────────────────────────────────────────────┘
```

### ASCII Fallback

For terminals without Nerd Fonts:

```
[C#] Using C# Code Reviewer
```

### Icon Reference Table

| Subagent | Icon Key | Nerd Font Code | Glyph | Fallback |
|----------|----------|----------------|-------|----------|
| C# Code Reviewer | csharp | `\ue7b2` |  | `[C#]` |
| Python Code Reviewer | python | `\ue235` |  | `[py]` |
| PySpark Code Reviewer | spark | `\ue7a6` |  | `[>>]` |
| TypeScript Code Reviewer | typescript | `\ue628` |  | `[TS]` |
| Defect Investigator | search | `\uf002` |  | `[?]` |
| Root Cause Analyzer | target | `\uf140` |  | `[*]` |
| Work Item Manager | clipboard | `\uf328` |  | `[#]` |
| Kusto Query Builder | chart | `\uf201` |  | `[~]` |

**Reference**: [Nerd Fonts Cheat Sheet](https://www.nerdfonts.com/cheat-sheet)

---

## Subagent Logging

For debugging and troubleshooting, all subagent selections and invocations are logged to the session log file.

### Log Events

| Event | Description | Log Level |
|-------|-------------|-----------|
| `SUBAGENT_START` | Subagent invocation begins | INFO |
| `SUBAGENT_COMPLETE` | Subagent completes successfully | INFO |
| `SUBAGENT_ERROR` | Subagent encounters an error | ERROR |
| `SUBAGENT_DETECTED` | Language/type auto-detected from PR files | DEBUG |

### Log Format

```
2025-12-31 15:30:45 - triagent.session.abc123 - INFO - SUBAGENT_START subagent=csharp-code-reviewer description="C# Code Reviewer" trigger="PR #123 file extensions" files_analyzed=8
2025-12-31 15:31:02 - triagent.session.abc123 - INFO - SUBAGENT_COMPLETE subagent=csharp-code-reviewer duration_ms=17000 result="4 issues found"
```

### Detection Log Example

```
2025-12-31 15:30:44 - triagent.session.abc123 - DEBUG - SUBAGENT_DETECTED extensions=[".cs", ".csproj"] matched_subagent=csharp-code-reviewer confidence=high
```

### Implementation

```python
# src/triagent/session_logger.py (additions)

def log_subagent_start(
    subagent_name: str,
    description: str,
    trigger: str,
    context: dict[str, Any] | None = None,
) -> None:
    """Log when a subagent is invoked.

    Args:
        subagent_name: The subagent identifier (e.g., "csharp-code-reviewer")
        description: Human-readable description (e.g., "C# Code Reviewer")
        trigger: What triggered the selection (e.g., "PR #123 file extensions")
        context: Additional context (files analyzed, etc.)
    """
    if _session_logger:
        ctx_str = ""
        if context:
            ctx_str = " " + " ".join(f"{k}={v}" for k, v in context.items())
        _session_logger.info(
            f'SUBAGENT_START subagent={subagent_name} '
            f'description="{description}" trigger="{trigger}"{ctx_str}'
        )


def log_subagent_complete(
    subagent_name: str,
    duration_ms: int,
    result_summary: str,
) -> None:
    """Log when a subagent completes.

    Args:
        subagent_name: The subagent identifier
        duration_ms: Duration of the subagent execution in milliseconds
        result_summary: Brief summary of the result
    """
    if _session_logger:
        _session_logger.info(
            f'SUBAGENT_COMPLETE subagent={subagent_name} '
            f'duration_ms={duration_ms} result="{result_summary}"'
        )


def log_subagent_error(
    subagent_name: str,
    error: str,
) -> None:
    """Log when a subagent encounters an error.

    Args:
        subagent_name: The subagent identifier
        error: Error message
    """
    if _session_logger:
        _session_logger.error(
            f'SUBAGENT_ERROR subagent={subagent_name} error="{error}"'
        )


def log_subagent_detected(
    extensions: list[str],
    matched_subagent: str,
    confidence: str = "high",
) -> None:
    """Log language/type detection for auto-routing.

    Args:
        extensions: File extensions that were analyzed
        matched_subagent: The subagent selected based on detection
        confidence: Detection confidence level
    """
    if _session_logger:
        _session_logger.debug(
            f'SUBAGENT_DETECTED extensions={extensions} '
            f'matched_subagent={matched_subagent} confidence={confidence}'
        )
```

### Integration with Subagent Visibility

The logging integrates with the subagent visibility hooks:

```python
# src/triagent/hooks/subagent_visibility.py

import time
from ..session_logger import (
    log_subagent_start,
    log_subagent_complete,
    log_subagent_error,
)

_subagent_start_times: dict[str, float] = {}

def show_subagent_start(
    console: Console,
    subagent_type: str,
    use_nerd_fonts: bool = True,
    trigger: str = "",
    context: dict | None = None,
) -> None:
    """Display which subagent is being used and log the invocation."""
    icon_key, name = SUBAGENT_DISPLAY.get(
        subagent_type,
        ("default", subagent_type.replace("-", " ").title())
    )
    icon = _get_icon(icon_key, use_nerd_fonts)
    console.print(f"\n{icon} [bold cyan]Using {name}[/bold cyan]")

    # Log the invocation
    _subagent_start_times[subagent_type] = time.time()
    log_subagent_start(subagent_type, name, trigger, context)


def show_subagent_complete(
    console: Console,
    subagent_type: str,
    result_summary: str,
    use_nerd_fonts: bool = True,
) -> None:
    """Display subagent completion and log the result."""
    icon_key, name = SUBAGENT_DISPLAY.get(
        subagent_type,
        ("default", subagent_type.replace("-", " ").title())
    )
    console.print(f"✓ [green]{name} complete[/green]: {result_summary}")

    # Log the completion
    start_time = _subagent_start_times.pop(subagent_type, None)
    duration_ms = int((time.time() - start_time) * 1000) if start_time else 0
    log_subagent_complete(subagent_type, duration_ms, result_summary)
```

### Log File Location

Session logs are stored in platform-specific directories:
- **macOS**: `~/Library/Logs/triagent/sessions/`
- **Windows**: `%LOCALAPPDATA%/triagent/logs/sessions/`
- **Linux**: `~/.local/share/triagent/logs/sessions/`

The `latest.log` symlink always points to the most recent session log.

---

## Language Detection

When user says "review PR #123", Claude automatically detects the programming language.

### Detection Flow

1. Claude calls `mcp__azure-devops__get_pull_request_changes`
2. Analyzes file extensions to determine primary language
3. Invokes the appropriate code reviewer subagent

### File Extension Mapping

```python
FILE_EXTENSION_MAP = {
    # C# / .NET
    ".cs": "csharp-code-reviewer",
    ".csproj": "csharp-code-reviewer",
    ".sln": "csharp-code-reviewer",

    # Python
    ".py": "python-code-reviewer",
    ".pyi": "python-code-reviewer",
    ".ipynb": "pyspark-code-reviewer",  # Notebooks → PySpark

    # TypeScript / JavaScript
    ".ts": "typescript-code-reviewer",
    ".tsx": "typescript-code-reviewer",
    ".js": "typescript-code-reviewer",
    ".jsx": "typescript-code-reviewer",
}
```

### Subagent Routing Table

| User Says | Detection Method | Subagent Invoked |
|-----------|-----------------|------------------|
| "Review PR #123" | File extensions (.cs, .csproj) | csharp-code-reviewer |
| "Review PR #456" | File extensions (.py) | python-code-reviewer |
| "Review PR #789" | File extensions (.ipynb) | pyspark-code-reviewer |
| "Review PR #321" | File extensions (.ts, .tsx) | typescript-code-reviewer |

---

## File Structure

```
src/triagent/
├── config.py                       # Add persona, use_nerd_fonts fields
├── sdk_client.py                   # Add persona support, agents
│
├── commands/
│   ├── init.py                     # Add persona selection step
│   └── persona.py                  # NEW: /persona command
│
├── hooks/
│   └── subagent_visibility.py      # NEW: Nerd Font icon display
│
└── skills/
    ├── __init__.py                 # Package exports
    ├── models.py                   # Data models
    ├── loader.py                   # Skill/persona loading
    │
    ├── core/                       # Shared skills
    │   ├── ado_basics.md
    │   ├── telemetry_basics.md
    │   └── _subagents/
    │       ├── kusto_query_builder.yaml
    │       └── ado_navigator.yaml
    │
    └── omnia-data/                 # Team-specific
        ├── _persona_developer.yaml
        ├── _persona_support.yaml
        ├── _subagents/
        │   ├── csharp_code_reviewer.yaml
        │   ├── python_code_reviewer.yaml
        │   └── pyspark_code_reviewer.yaml
        │
        ├── developer/
        │   ├── dotnet_code_review.md
        │   ├── python_code_review.md
        │   ├── pyspark_code_review.md
        │   ├── ado_pr_review.md
        │   └── release_investigation.md
        │
        └── support/
            ├── telemetry_investigation.md
            ├── root_cause_analysis.md
            ├── ado_work_items.md
            └── lsi_creation.md
```

---

## Data Models

### SkillMetadata (YAML Frontmatter)

```yaml
---
name: dotnet_code_review
display_name: ".NET Code Review"
description: "Review .NET/C# code changes in PRs"
version: "1.0.0"
tags: [code-review, dotnet, csharp]
requires: [ado_basics]
subagents: [csharp_code_reviewer]
tools: [Read, Glob, Grep, mcp__azure-devops__add_pull_request_comment]
triggers: ["review.*\\.cs", "review.*dotnet"]
---

## .NET Code Review Guidelines
[Skill content here...]
```

### PersonaDefinition (YAML)

```yaml
# _persona_developer.yaml
name: developer
display_name: "Developer"
description: "Code review, PR management, release investigation"

core_skills:
  - ado_basics
  - telemetry_basics

skills:
  - dotnet_code_review
  - python_code_review
  - pyspark_code_review
  - ado_pr_review
  - release_investigation

system_prompt_additions: |
  ## Developer Persona Context
  You are assisting a developer with code-focused tasks...

default_model: sonnet
```

### SubagentConfig (YAML)

```yaml
# _subagents/csharp_code_reviewer.yaml
name: csharp-code-reviewer
description: |
  Expert C#/.NET code reviewer. Use this agent when:
  - User asks to review a PR containing .cs, .csproj, or .sln files
  - User mentions C#, .NET, ASP.NET, or Entity Framework
  Automatically detect from PR file extensions.

prompt: |
  You are a senior C#/.NET code reviewer...

tools:
  - Read
  - Glob
  - Grep
  - mcp__azure-devops__add_pull_request_comment

model: sonnet

file_extensions:
  - .cs
  - .csproj
  - .sln
```

---

## Implementation Phases

### Phase 1: Core Infrastructure

| Task | File | Description |
|------|------|-------------|
| 1.1 | `config.py` | Add `persona` and `use_nerd_fonts` fields |
| 1.2 | `skills/models.py` | Create data models |
| 1.3 | `skills/loader.py` | Create skill/persona loader |
| 1.4 | `skills/__init__.py` | Create package exports |
| 1.5 | `pyproject.toml` | Add PyYAML dependency |

### Phase 2: CLI Integration

| Task | File | Description |
|------|------|-------------|
| 2.1 | `commands/init.py` | Add persona selection step (Step 3/6) |
| 2.2 | `commands/persona.py` | Create /persona command |
| 2.3 | `cli.py` | Register /persona, update header |

### Phase 3: SDK Integration

| Task | File | Description |
|------|------|-------------|
| 3.1 | `prompts/system.py` | Include persona in system prompt |
| 3.2 | `sdk_client.py` | Add persona, pass agents to SDK |
| 3.3 | `hooks/subagent_visibility.py` | Create Nerd Font icon display |

### Phase 4: Skills Content

| Task | Directory | Description |
|------|-----------|-------------|
| 4.1 | `skills/core/` | Create shared ADO, Telemetry skills |
| 4.2 | `skills/omnia-data/developer/` | Create developer skills |
| 4.3 | `skills/omnia-data/support/` | Create support skills |
| 4.4 | `skills/omnia-data/_subagents/` | Create subagent configs |

### Phase 5: Testing

| Task | File | Description |
|------|------|-------------|
| 5.1 | `tests/test_skills.py` | Skill loader unit tests |
| 5.2 | `tests/test_personas.py` | Persona config tests |
| 5.3 | `tests/test_visibility.py` | Subagent visibility tests |

---

## Acceptance Criteria

### Persona & Skills

- [ ] `/init` shows persona selection after team selection (Step 3/6)
- [ ] `/persona` command shows current persona and allows switching
- [ ] Persona switch reinitializes SDK with new subagents
- [ ] Developer persona loads code review skills and subagents
- [ ] Support persona loads telemetry/RCA skills and subagents
- [ ] Existing team CLAUDE.md content preserved in Support persona
- [ ] Backward compatible with configs without `persona` field

### Subagent Visibility

- [ ] User sees which subagent is handling their request with Nerd Font icons
- [ ] Subagent start indicator shown when Task tool invokes subagent
- [ ] Subagent completion indicator shown with result summary
- [ ] Subagent type correctly identified from Task tool input
- [ ] Nerd Font icons render correctly (requires Nerd Font installed)
- [ ] ASCII fallback works when `use_nerd_fonts=False`

### Code Review Functionality

- [ ] User saying "review PR #123" automatically detects language from file extensions
- [ ] Claude fetches PR files, analyzes extensions, and invokes correct subagent
- [ ] Code reviewer provides file path, line number, severity, and fix suggestion
- [ ] Inline comments posted to ADO PR with proper formatting
- [ ] Subagent descriptions include file extension patterns for accurate routing

### Subagent Logging

- [ ] `SUBAGENT_START` logged when subagent is invoked
- [ ] `SUBAGENT_COMPLETE` logged with duration and result summary
- [ ] `SUBAGENT_ERROR` logged when subagent encounters an error
- [ ] `SUBAGENT_DETECTED` logged at DEBUG level for auto-detection
- [ ] Logs written to platform-specific session log directory
- [ ] Log format follows existing session logger conventions

### Testing

- [ ] Unit tests for skill loader (frontmatter parsing, skill loading)
- [ ] Unit tests for persona config (load, save, switch)
- [ ] Integration tests for subagent visibility
- [ ] Unit tests for subagent logging functions
- [ ] All existing tests pass

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-31 | Santosh Dandey | Initial design document |
| 1.1 | 2025-12-31 | Santosh Dandey | Added subagent logging section for debugging |
