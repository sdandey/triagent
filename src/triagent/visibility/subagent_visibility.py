"""Subagent visibility hooks for Triagent CLI.

This module provides visual indicators for when Claude invokes subagents,
using Nerd Font icons with ASCII fallback for terminals without Nerd Fonts.

Reference: https://www.nerdfonts.com/cheat-sheet
"""

from __future__ import annotations

import time
from typing import Any

from rich.console import Console

from triagent.session_logger import (
    log_subagent_complete,
    log_subagent_error,
    log_subagent_start,
)

# Nerd Font icons (Devicons + Font Awesome)
# Reference: https://www.nerdfonts.com/cheat-sheet
# Devicons: E700-E8EF, Font Awesome: F000-F2E0
NERD_FONT_ICONS = {
    "python": "\ue235",      # nf-dev-python (Devicons)
    "csharp": "\ue7b2",      # nf-dev-csharp (Devicons)
    "typescript": "\ue628",  # nf-dev-typescript (Devicons)
    "javascript": "\ue74e",  # nf-dev-javascript (Devicons)
    "spark": "\ue7a6",       # nf-dev-scala (Devicons) - closest to Spark
    "search": "\uf002",      # nf-fa-search (Font Awesome)
    "bug": "\uf188",         # nf-fa-bug (Font Awesome)
    "target": "\uf140",      # nf-fa-bullseye (Font Awesome)
    "clipboard": "\uf328",   # nf-fa-clipboard (Font Awesome)
    "chart": "\uf201",       # nf-fa-chart_line (Font Awesome)
    "default": "\uf121",     # nf-fa-code (Font Awesome)
}

# Fallback ASCII icons for terminals without Nerd Fonts
ASCII_ICONS = {
    "python": "[py]",
    "csharp": "[C#]",
    "typescript": "[TS]",
    "javascript": "[JS]",
    "spark": "[>>]",
    "search": "[?]",
    "bug": "[!]",
    "target": "[*]",
    "clipboard": "[#]",
    "chart": "[~]",
    "default": "[>]",
}

# Subagent configuration with icon keys
# Maps subagent type to (icon_key, display_name)
SUBAGENT_DISPLAY = {
    "csharp-code-reviewer": ("csharp", "C# Code Reviewer"),
    "python-code-reviewer": ("python", "Python Code Reviewer"),
    "pyspark-code-reviewer": ("spark", "PySpark Code Reviewer"),
    "typescript-code-reviewer": ("typescript", "TypeScript Code Reviewer"),
    "defect-investigator": ("search", "Defect Investigator"),
    "rca-analyzer": ("target", "Root Cause Analyzer"),
    "work-item-manager": ("clipboard", "Work Item Manager"),
    "kusto-query-builder": ("chart", "Kusto Query Builder"),
}

# Track subagent start times for duration calculation
_subagent_start_times: dict[str, float] = {}


def _get_icon(icon_key: str, use_nerd_fonts: bool = True) -> str:
    """Get icon based on terminal capability.

    Args:
        icon_key: The icon key (e.g., "python", "csharp")
        use_nerd_fonts: If True, use Nerd Font icons; False uses ASCII

    Returns:
        The icon string
    """
    if use_nerd_fonts:
        return NERD_FONT_ICONS.get(icon_key, NERD_FONT_ICONS["default"])
    return ASCII_ICONS.get(icon_key, ASCII_ICONS["default"])


def show_subagent_start(
    console: Console,
    subagent_type: str,
    use_nerd_fonts: bool = True,
    trigger: str = "",
    context: dict[str, Any] | None = None,
) -> None:
    """Display which subagent is being used and log the invocation.

    Args:
        console: Rich console for output
        subagent_type: The subagent identifier (e.g., "csharp-code-reviewer")
        use_nerd_fonts: If True, use Nerd Font icons; False uses ASCII
        trigger: What triggered the subagent (e.g., "PR #123 file extensions")
        context: Additional context for logging
    """
    icon_key, name = SUBAGENT_DISPLAY.get(
        subagent_type,
        ("default", subagent_type.replace("-", " ").title())
    )
    icon = _get_icon(icon_key, use_nerd_fonts)

    # Display visual indicator
    console.print(f"\n{icon} [bold cyan]Using {name}[/bold cyan]")

    # Track start time for duration calculation
    _subagent_start_times[subagent_type] = time.time()

    # Log the invocation
    log_subagent_start(subagent_type, name, trigger, context)


def show_subagent_complete(
    console: Console,
    subagent_type: str,
    result_summary: str,
    use_nerd_fonts: bool = True,
    is_error: bool = False,
) -> None:
    """Display subagent completion status and log the result.

    Args:
        console: Rich console for output
        subagent_type: The subagent identifier
        result_summary: Brief summary of the result
        use_nerd_fonts: If True, use Nerd Font icons; False uses ASCII
        is_error: If True, this was an error completion
    """
    icon_key, name = SUBAGENT_DISPLAY.get(
        subagent_type,
        ("default", subagent_type.replace("-", " ").title())
    )

    # Display completion indicator
    if is_error:
        console.print(f"[red]✗ {name} failed[/red]: {result_summary}")
    else:
        console.print(f"[green]✓ {name} complete[/green]: {result_summary}")

    # Calculate duration
    start_time = _subagent_start_times.pop(subagent_type, None)
    duration_ms = int((time.time() - start_time) * 1000) if start_time else 0

    # Log the completion
    if is_error:
        log_subagent_error(subagent_type, result_summary)
    else:
        log_subagent_complete(subagent_type, duration_ms, result_summary)


def get_subagent_display_info(subagent_type: str) -> tuple[str, str]:
    """Get display information for a subagent type.

    Args:
        subagent_type: The subagent identifier

    Returns:
        Tuple of (icon_key, display_name)
    """
    return SUBAGENT_DISPLAY.get(
        subagent_type,
        ("default", subagent_type.replace("-", " ").title())
    )
