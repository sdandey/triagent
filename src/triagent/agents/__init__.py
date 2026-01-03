"""Triagent subagents module.

This module contains specialized subagents for specific tasks:
- Defect Investigation: Analyze defects/incidents and generate Kusto queries
- PR Code Review: Review pull requests for code quality and best practices
"""

from triagent.agents.defect_investigator import (
    DEFECT_INVESTIGATOR_CONFIG,
    DEFECT_INVESTIGATOR_PROMPT,
)
from triagent.agents.pr_code_reviewer import (
    PR_CODE_REVIEWER_CONFIG,
    PR_CODE_REVIEWER_PROMPT,
)

__all__ = [
    "DEFECT_INVESTIGATOR_CONFIG",
    "DEFECT_INVESTIGATOR_PROMPT",
    "PR_CODE_REVIEWER_CONFIG",
    "PR_CODE_REVIEWER_PROMPT",
]
