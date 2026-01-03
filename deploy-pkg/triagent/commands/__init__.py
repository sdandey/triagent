"""Triagent slash commands."""

from triagent.commands.config import config_command
from triagent.commands.help import help_command
from triagent.commands.init import init_command
from triagent.commands.team import team_command
from triagent.commands.team_report import team_report_command

__all__ = [
    "init_command",
    "help_command",
    "config_command",
    "team_command",
    "team_report_command",
]
