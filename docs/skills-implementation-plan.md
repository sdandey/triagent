# Triagent Skills & Persona Implementation Plan

**Document Version:** 1.0
**Prepared by:** sdandey
**Last Updated:** 2025-12-31 13:21:46
**GitHub Issue:** [#10](https://github.com/sdandey/triagent/issues/10)
**Branch:** feature/skills-implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [User Persona Flow](#user-persona-flow)
3. [Architecture Design](#architecture-design)
4. [Implementation Tasks](#implementation-tasks)
5. [Skill Development Tasks](#skill-development-tasks)
6. [Testing Strategy](#testing-strategy)
7. [Acceptance Criteria](#acceptance-criteria)
8. [Document History](#document-history)

---

## Executive Summary

This document outlines the implementation plan for adding a persona-based skill system to Triagent CLI. The system enables team-specific personas (Developer, Support) with composed skill sets, where each skill can define specialized subagents that are automatically invoked based on user requests.

### Goals

- Enable role-based workflows (Developer vs Support)
- Modular skill composition with YAML frontmatter metadata
- Dynamic subagent invocation via Claude Agent SDK
- Runtime persona switching without restart

### MVP Scope

- **Team**: omnia-data only
- **Personas**: Developer, Support
- **Skills**: 10 skills (2 core + 5 developer + 3 support)

---

## User Persona Flow

### Initialization Flow

:::mermaid
graph TD
    A[User runs triagent] --> B{Config exists?}
    B -->|No| C[Run /init wizard]
    B -->|Yes| D[Load existing config]

    C --> E[Step 1: API Provider Selection]
    E --> F[Step 2: Team Selection]
    F --> G[Step 3: Persona Selection]
    G --> H[Step 4: MCP Server Setup]
    H --> I[Step 5: Azure Authentication]
    I --> J[Step 6: Prerequisites Check]
    J --> K[Save config.json]

    K --> L[Initialize SDK Client]
    D --> L
    L --> M[Load Persona Skills]
    M --> N[Build Agent Definitions]
    N --> O[Start Interactive Loop]

    O --> P{User Input}
    P -->|/persona| Q[Persona Switch Flow]
    P -->|Message| R[Process with Subagents]

    Q --> S[Show persona options]
    S --> T[User selects persona]
    T --> U[Update config]
    U --> V[Reinitialize SDK Client]
    V --> O
:::

### Persona Selection UI Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   Step 3/6: Persona Selection               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Select your workflow persona:                              │
│                                                             │
│    1. Developer                                             │
│       Code review, PR management, release investigation     │
│                                                             │
│    2. Support Engineer                                      │
│       Defect investigation, telemetry analysis, incidents   │
│                                                             │
│  Enter persona number (1-2): _                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Runtime Persona Switch Flow

```
┌─────────────────────────────────────────────────────────────┐
│  User: /persona                                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Current Persona                            │    │
│  │  Persona: Developer                                  │    │
│  │  Description: Code review, PR management...          │    │
│  │  Subagents: dotnet-reviewer, python-reviewer...      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  Available personas for this team:                          │
│    - developer: Developer (current)                         │
│    - support: Support Engineer                              │
│                                                             │
│  Usage: /persona <name> to switch personas                  │
├─────────────────────────────────────────────────────────────┤
│  User: /persona support                                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Switched persona: Support Engineer                  │    │
│  │  From: developer -> To: support                      │    │
│  │  Reinitializing SDK client with new subagents...     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Design

### High-Level Architecture

:::mermaid
graph TB
    subgraph "User Interface"
        CLI[CLI - cli.py]
        INIT[/init Command]
        PERSONA[/persona Command]
    end

    subgraph "Configuration Layer"
        CONFIG[TriagentConfig]
        CREDS[TriagentCredentials]
        CONFIGMGR[ConfigManager]
    end

    subgraph "Skills Engine"
        LOADER[SkillLoader]
        MODELS[SkillModels]
        REGISTRY[SkillRegistry]
    end

    subgraph "Skills Storage"
        CORE[core/ - ADO + Telemetry]
        DEVSKILLS[developer/ - Code Review Skills]
        SUPSKILLS[support/ - Investigation Skills]
        SUBAGENTS[_subagents/ - Python Configs]
    end

    subgraph "SDK Integration"
        SDKCLIENT[TriagentSDKClient]
        SYSPROMPT[System Prompt Builder]
        AGENTDEFS[AgentDefinitions]
    end

    subgraph "Claude Agent SDK"
        SDK[ClaudeSDKClient]
        TASK[Task Tool - Subagent Invocation]
    end

    CLI --> CONFIGMGR
    INIT --> CONFIG
    PERSONA --> CONFIG

    CONFIGMGR --> LOADER
    LOADER --> CORE
    LOADER --> DEVSKILLS
    LOADER --> SUPSKILLS
    LOADER --> SUBAGENTS

    LOADER --> MODELS
    MODELS --> AGENTDEFS

    SDKCLIENT --> SYSPROMPT
    SDKCLIENT --> AGENTDEFS
    SDKCLIENT --> SDK

    SDK --> TASK
:::

### Skills Directory Structure

```
src/triagent/skills/
├── __init__.py                    # Package exports
├── models.py                      # Data models (SkillMetadata, SubagentConfig, etc.)
├── loader.py                      # Skill loading and composition logic
│
├── core/                          # Core skills (shared by all personas)
│   ├── ado_basics.md             # ADO repository, PR, pipeline basics
│   ├── telemetry_basics.md       # Kusto query fundamentals
│   └── _subagents/
│       ├── kusto_query_builder.py
│       └── ado_navigator.py
│
└── omnia-data/                    # Team-specific skills (MVP)
    ├── _persona_developer.yaml    # Developer persona definition
    ├── _persona_support.yaml      # Support persona definition
    │
    ├── developer/                 # Developer-specific skills
    │   ├── dotnet_code_review.md
    │   ├── python_code_review.md
    │   ├── pyspark_code_review.md
    │   ├── ado_pr_review.md
    │   ├── release_investigation.md
    │   └── _subagents/
    │       ├── dotnet_analyzer.py
    │       ├── python_analyzer.py
    │       ├── pyspark_analyzer.py
    │       ├── pr_commenter.py
    │       └── pipeline_investigator.py
    │
    └── support/                   # Support-specific skills
        ├── telemetry_investigation.md
        ├── root_cause_analysis.md
        ├── ado_work_items.md
        ├── lsi_creation.md
        └── _subagents/
            ├── defect_investigator.py
            ├── rca_analyzer.py
            └── work_item_manager.py
```

### Data Flow

:::mermaid
sequenceDiagram
    participant User
    participant CLI
    participant ConfigMgr
    participant SkillLoader
    participant SDKClient
    participant ClaudeSDK
    participant Subagent

    User->>CLI: Start triagent
    CLI->>ConfigMgr: Load config (team, persona)
    ConfigMgr-->>CLI: TriagentConfig

    CLI->>SkillLoader: load_persona(team, persona)
    SkillLoader->>SkillLoader: Load core skills
    SkillLoader->>SkillLoader: Load persona skills
    SkillLoader->>SkillLoader: Load subagent configs
    SkillLoader-->>CLI: LoadedPersona

    CLI->>SDKClient: Create with persona
    SDKClient->>SDKClient: Build system prompt
    SDKClient->>SDKClient: Build AgentDefinitions
    SDKClient-->>CLI: ClaudeAgentOptions

    User->>CLI: "Review the .NET code in PR #123"
    CLI->>ClaudeSDK: query(message)
    ClaudeSDK->>ClaudeSDK: Match to dotnet-code-reviewer subagent
    ClaudeSDK->>Subagent: Task tool invocation
    Subagent->>Subagent: Execute code review
    Subagent-->>ClaudeSDK: Review results
    ClaudeSDK-->>CLI: Response with PR comments
    CLI-->>User: Display results
:::

### Skill Composition Model

:::mermaid
graph LR
    subgraph "Persona: Developer"
        P1[PersonaDefinition]
    end

    subgraph "Core Skills"
        CS1[ado_basics.md]
        CS2[telemetry_basics.md]
    end

    subgraph "Developer Skills"
        DS1[dotnet_code_review.md]
        DS2[python_code_review.md]
        DS3[pyspark_code_review.md]
        DS4[ado_pr_review.md]
        DS5[release_investigation.md]
    end

    subgraph "Subagents"
        SA1[kusto_query_builder]
        SA2[ado_navigator]
        SA3[dotnet_analyzer]
        SA4[python_analyzer]
        SA5[pyspark_analyzer]
        SA6[pr_commenter]
        SA7[pipeline_investigator]
    end

    P1 --> CS1
    P1 --> CS2
    P1 --> DS1
    P1 --> DS2
    P1 --> DS3
    P1 --> DS4
    P1 --> DS5

    CS1 --> SA2
    CS2 --> SA1
    DS1 --> SA3
    DS2 --> SA4
    DS3 --> SA5
    DS4 --> SA6
    DS5 --> SA7
:::

---

## Implementation Tasks

### Phase 1: Core Infrastructure

| Task ID | Task | Files | Estimate |
|---------|------|-------|----------|
| INFRA-1 | Add `persona` field to TriagentConfig | `src/triagent/config.py` | S |
| INFRA-2 | Create skills data models | `src/triagent/skills/models.py` | M |
| INFRA-3 | Create skill loader with YAML parsing | `src/triagent/skills/loader.py` | M |
| INFRA-4 | Create skills package init | `src/triagent/skills/__init__.py` | S |
| INFRA-5 | Add PyYAML dependency | `pyproject.toml` | S |

### Phase 2: CLI Integration

| Task ID | Task | Files | Estimate |
|---------|------|-------|----------|
| CLI-1 | Add persona selection to /init flow | `src/triagent/commands/init.py` | M |
| CLI-2 | Create /persona command | `src/triagent/commands/persona.py` | M |
| CLI-3 | Register /persona in CLI handler | `src/triagent/cli.py` | S |
| CLI-4 | Update header to show current persona | `src/triagent/cli.py` | S |
| CLI-5 | Handle SDK restart after persona switch | `src/triagent/cli.py` | S |

### Phase 3: SDK Integration

| Task ID | Task | Files | Estimate |
|---------|------|-------|----------|
| SDK-1 | Update system prompt builder for persona | `src/triagent/prompts/system.py` | M |
| SDK-2 | Add persona to TriagentSDKClient | `src/triagent/sdk_client.py` | M |
| SDK-3 | Build AgentDefinitions from persona | `src/triagent/sdk_client.py` | M |

### Phase 4: Testing

| Task ID | Task | Files | Estimate |
|---------|------|-------|----------|
| TEST-1 | Unit tests for skill loader | `tests/test_skills.py` | M |
| TEST-2 | Unit tests for persona config | `tests/test_personas.py` | M |
| TEST-3 | Integration tests for persona flow | `tests/test_cli_integration.py` | L |

---

## Skill Development Tasks

Each skill follows a **Research → Create → Test** workflow.

### Core Skills

#### SKILL-CORE-1: ADO Basics Skill

| Phase | Task | Details |
|-------|------|---------|
| **Research** | Study ADO MCP tools | Review `mcp__azure-devops__*` tools available in sdk_client.py |
| **Research** | Identify common patterns | Repository navigation, PR operations, pipeline queries |
| **Create** | Write `core/ado_basics.md` | YAML frontmatter + ADO navigation instructions |
| **Create** | Write `core/_subagents/ado_navigator.py` | Subagent for ADO structure navigation |
| **Test** | Unit test skill loading | Verify frontmatter parsing and subagent resolution |
| **Test** | Integration test | Test subagent invocation with sample ADO queries |

#### SKILL-CORE-2: Telemetry Basics Skill

| Phase | Task | Details |
|-------|------|---------|
| **Research** | Review omnia_data.md telemetry section | Extract Log Analytics tables, workspace IDs, query patterns |
| **Research** | Study Kusto query patterns | Common exception queries, request analysis, dependency tracing |
| **Create** | Write `core/telemetry_basics.md` | YAML frontmatter + Kusto fundamentals |
| **Create** | Write `core/_subagents/kusto_query_builder.py` | Subagent for generating optimized Kusto queries |
| **Test** | Unit test skill loading | Verify frontmatter parsing |
| **Test** | Integration test | Test Kusto query generation for various scenarios |

### Developer Persona Skills

#### SKILL-DEV-1: .NET Code Review Skill

| Phase | Task | Details |
|-------|------|---------|
| **Research** | Study .NET/C# best practices | SOLID, async patterns, null safety, exception handling |
| **Research** | Review existing code review patterns | ADO PR comment format, inline comment structure |
| **Research** | Identify common .NET issues | Performance anti-patterns, security vulnerabilities |
| **Create** | Write `omnia-data/developer/dotnet_code_review.md` | YAML frontmatter with triggers for .cs files |
| **Create** | Write `_subagents/dotnet_analyzer.py` | Expert .NET reviewer subagent |
| **Test** | Unit test skill loading | Verify trigger patterns work |
| **Test** | E2E test | Review sample C# PR and verify comments |

#### SKILL-DEV-2: Python Code Review Skill

| Phase | Task | Details |
|-------|------|---------|
| **Research** | Study Python best practices | PEP8, type hints, async patterns, error handling |
| **Research** | Review existing Python codebases | Patterns used in triagent, cortexpy |
| **Create** | Write `omnia-data/developer/python_code_review.md` | YAML frontmatter with triggers for .py files |
| **Create** | Write `_subagents/python_analyzer.py` | Expert Python reviewer subagent |
| **Test** | Unit test skill loading | Verify trigger patterns |
| **Test** | E2E test | Review sample Python PR |

#### SKILL-DEV-3: PySpark Code Review Skill

| Phase | Task | Details |
|-------|------|---------|
| **Research** | Study PySpark best practices | DataFrame operations, UDFs, partitioning, optimization |
| **Research** | Review Databricks patterns | Unity Catalog, Delta Lake, notebook patterns |
| **Create** | Write `omnia-data/developer/pyspark_code_review.md` | YAML frontmatter with Spark-specific triggers |
| **Create** | Write `_subagents/pyspark_analyzer.py` | Expert PySpark reviewer subagent |
| **Test** | Unit test skill loading | Verify triggers for PySpark patterns |
| **Test** | E2E test | Review sample PySpark code |

#### SKILL-DEV-4: ADO PR Review Skill

| Phase | Task | Details |
|-------|------|---------|
| **Research** | Study ADO PR comment API | Thread creation, inline comments, status updates |
| **Research** | Review add_pr_inline_comments.sh | Existing helper script patterns |
| **Create** | Write `omnia-data/developer/ado_pr_review.md` | YAML frontmatter with PR review workflow |
| **Create** | Write `_subagents/pr_commenter.py` | Subagent for adding inline PR comments |
| **Test** | Unit test skill loading | Verify MCP tool references |
| **Test** | E2E test | Add comments to test PR |

#### SKILL-DEV-5: Release Investigation Skill

| Phase | Task | Details |
|-------|------|---------|
| **Research** | Study pipeline failure patterns | Common causes, log analysis patterns |
| **Research** | Review pipeline MCP tools | `get_pipeline_log`, `pipeline_timeline`, etc. |
| **Create** | Write `omnia-data/developer/release_investigation.md` | YAML frontmatter with investigation workflow |
| **Create** | Write `_subagents/pipeline_investigator.py` | Subagent for pipeline failure analysis |
| **Test** | Unit test skill loading | Verify tool references |
| **Test** | E2E test | Investigate sample failed pipeline |

### Support Persona Skills

#### SKILL-SUP-1: Telemetry Investigation Skill

| Phase | Task | Details |
|-------|------|---------|
| **Research** | Review omnia_data.md investigation patterns | Exception analysis, request tracing, dependency failures |
| **Research** | Study defect_investigator.py | Existing investigation workflow |
| **Create** | Write `omnia-data/support/telemetry_investigation.md` | YAML frontmatter with investigation workflow |
| **Create** | Write `_subagents/defect_investigator.py` | Migrate existing defect investigator |
| **Test** | Unit test skill loading | Verify telemetry table references |
| **Test** | E2E test | Investigate sample exception |

#### SKILL-SUP-2: Root Cause Analysis Skill

| Phase | Task | Details |
|-------|------|---------|
| **Research** | Study RCA methodologies | 5 Whys, fishbone diagrams, timeline analysis |
| **Research** | Identify cross-service patterns | Request correlation, dependency chains |
| **Create** | Write `omnia-data/support/root_cause_analysis.md` | YAML frontmatter with RCA workflow |
| **Create** | Write `_subagents/rca_analyzer.py` | Subagent for systematic RCA |
| **Test** | Unit test skill loading | Verify workflow steps |
| **Test** | E2E test | Perform RCA on sample incident |

#### SKILL-SUP-3: ADO Work Items Skill

| Phase | Task | Details |
|-------|------|---------|
| **Research** | Review ADO work item types | Defect, Incident, LSI, Task templates |
| **Research** | Study work item MCP tools | `create_work_item`, `update_work_item`, `manage_work_item_link` |
| **Create** | Write `omnia-data/support/ado_work_items.md` | YAML frontmatter with work item templates |
| **Create** | Write `_subagents/work_item_manager.py` | Subagent for work item CRUD |
| **Test** | Unit test skill loading | Verify work item templates |
| **Test** | E2E test | Create and update sample work item |

---

## Testing Strategy

### Unit Tests

```python
# tests/test_skills.py
class TestFrontmatterParsing:
    def test_parse_valid_frontmatter(self): ...
    def test_parse_missing_frontmatter(self): ...
    def test_parse_invalid_yaml(self): ...

class TestSkillLoading:
    def test_load_skill_from_path(self): ...
    def test_load_skill_with_subagents(self): ...
    def test_skill_dependency_resolution(self): ...

class TestPersonaLoading:
    def test_load_developer_persona(self): ...
    def test_load_support_persona(self): ...
    def test_persona_skill_composition(self): ...

class TestAgentDefinitionGeneration:
    def test_generate_agent_definitions(self): ...
    def test_subagent_description_format(self): ...
```

### Integration Tests

```python
# tests/test_personas.py
class TestPersonaConfig:
    def test_persona_in_config(self): ...
    def test_persona_defaults_to_developer(self): ...
    def test_backward_compatible_config(self): ...

class TestPersonaSelection:
    def test_available_personas_for_team(self): ...
    def test_persona_switch_updates_config(self): ...
```

---

## Acceptance Criteria

### Functional Requirements

- [ ] **AC-1**: `/init` wizard includes persona selection step after team selection
- [ ] **AC-2**: `/persona` command displays current persona and available options
- [ ] **AC-3**: `/persona <name>` switches persona and reinitializes SDK client
- [ ] **AC-4**: Developer persona loads all developer skills and subagents
- [ ] **AC-5**: Support persona loads all support skills and subagents
- [ ] **AC-6**: User message "review the .NET code" triggers dotnet-code-reviewer subagent
- [ ] **AC-7**: User message "investigate defect #123" triggers defect-investigator subagent
- [ ] **AC-8**: Existing omnia_data.md content is preserved in Support persona
- [ ] **AC-9**: Config without `persona` field defaults to "developer" (backward compatible)

### Technical Requirements

- [ ] **AC-10**: All skills have valid YAML frontmatter with required fields
- [ ] **AC-11**: Subagent descriptions are clear and trigger appropriate matching
- [ ] **AC-12**: Core skills are loaded before persona-specific skills
- [ ] **AC-13**: SkillLoader caches loaded skills for performance
- [ ] **AC-14**: Unit tests achieve >80% coverage for skills module
- [ ] **AC-15**: All existing CLI tests continue to pass

### Non-Functional Requirements

- [ ] **AC-16**: Persona switch completes within 2 seconds
- [ ] **AC-17**: Skill loading adds <500ms to startup time
- [ ] **AC-18**: Documentation includes user flow diagrams

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-31 | sdandey | Initial document creation |
