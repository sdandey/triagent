# Omnia Data Team - Claude Code Skills

Shareable skills for the Omnia Data team to use with Claude Code CLI.

## Available Skills

| Skill | Description | Invocation |
|-------|-------------|------------|
| **omnia-data** | Team context, telemetry config, pipelines, services | `/omnia-data` |
| **pyspark-reviewer** | Autonomous PySpark/Databricks code review | `/pyspark-reviewer` |

## Installation

### Quick Install (Recommended)

```bash
# Copy skills to your Claude Code skills directory
cp -r omnia-data pyspark-reviewer ~/.claude/skills/

# Verify installation
ls ~/.claude/skills/
# Should show: omnia-data/  pyspark-reviewer/
```

### Manual Install

1. Create the skills directory if it doesn't exist:
   ```bash
   mkdir -p ~/.claude/skills
   ```

2. Copy each skill folder:
   ```bash
   cp -r omnia-data ~/.claude/skills/
   cp -r pyspark-reviewer ~/.claude/skills/
   ```

## Usage

### omnia-data Skill

Load team context and reference information:

```
/omnia-data
```

Then ask questions like:
- "What's the workspace ID for EMA PRD?"
- "Which team owns data-kitchen-service?"
- "Show me the helm pipeline for 9.5"
- "How do I query AME production logs?"

**What it includes:**
- Azure DevOps repositories and contributors
- Telemetry configuration (App Insights, Log Analytics workspace IDs)
- Release pipeline patterns and naming conventions
- Service name mappings (CloudRoleName to repository)
- Team structure and area paths
- Kusto query templates

### pyspark-reviewer Skill

Autonomous code review for PySpark/Databricks code:

```
/pyspark-reviewer https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_git/cortexpy/pullrequest/12345
```

Or review local files:
```
/pyspark-reviewer src/jobs/etl_pipeline.py src/notebooks/data_transform.ipynb
```

**What it checks:**
- Performance: UDFs, joins, partitioning, caching
- Data Quality: Schema, null handling, validation
- Security: Credentials, Unity Catalog usage
- Code Quality: Method chaining, column references
- Serverless Compatibility: Caching, UDF types

**Output:**
- Categorized issues (Critical/High/Medium/Low)
- Specific line numbers and code snippets
- Suggested fixes with code examples
- Serverless compatibility checklist

## Skill Structure

Each skill follows the Claude Code skill format:

```
~/.claude/skills/
├── omnia-data/
│   └── SKILL.md          # Team context and reference
└── pyspark-reviewer/
    └── SKILL.md          # Code review agent
```

### SKILL.md Format

```markdown
---
name: skill-name
description: |
  When/how to use this skill...
version: 1.0.0
---

# Skill Content
[Instructions, reference tables, workflow steps]
```

## Updating Skills

To update to newer versions:

```bash
# Pull latest from shared location
cd /path/to/shareable-skills

# Overwrite existing skills
cp -r omnia-data pyspark-reviewer ~/.claude/skills/
```

## Troubleshooting

### Skills not showing up

1. Check the directory structure:
   ```bash
   ls -la ~/.claude/skills/
   ```

2. Verify SKILL.md exists in each folder:
   ```bash
   ls ~/.claude/skills/omnia-data/SKILL.md
   ls ~/.claude/skills/pyspark-reviewer/SKILL.md
   ```

### Skill not loading content

1. Check YAML frontmatter is valid (between `---` delimiters)
2. Ensure `name` field matches directory name
3. Restart Claude Code session

## Contributing

To add or update skills:

1. Edit the SKILL.md in the skill directory
2. Update the version in frontmatter
3. Copy to shareable-skills for distribution
4. Notify team of updates

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-01 | Initial release: omnia-data, pyspark-reviewer |
