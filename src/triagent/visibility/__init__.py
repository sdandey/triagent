"""Subagent visibility for Triagent CLI.

This module provides visual indicators and logging for subagent invocations,
using Nerd Font icons with ASCII fallback.
"""

from .subagent_visibility import (
    ASCII_ICONS,
    NERD_FONT_ICONS,
    SUBAGENT_DISPLAY,
    show_subagent_complete,
    show_subagent_start,
)

__all__ = [
    "NERD_FONT_ICONS",
    "ASCII_ICONS",
    "SUBAGENT_DISPLAY",
    "show_subagent_start",
    "show_subagent_complete",
]
