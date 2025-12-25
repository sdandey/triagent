"""Triagent subagents module.

This module contains specialized subagents for specific tasks:
- Defect Investigation: Analyze defects/incidents and generate Kusto queries
"""

from triagent.agents.defect_investigator import (
    DEFECT_INVESTIGATOR_CONFIG,
    DEFECT_INVESTIGATOR_PROMPT,
)

__all__ = [
    "DEFECT_INVESTIGATOR_CONFIG",
    "DEFECT_INVESTIGATOR_PROMPT",
]
