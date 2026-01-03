"""CLI adapters for unified command system.

These adapters implement the PromptContext and OutputContext protocols
using Rich for terminal rendering.
"""

from triagent.cli.adapters.prompt_adapter import CLIPromptAdapter
from triagent.cli.adapters.output_adapter import CLIOutputAdapter

__all__ = [
    "CLIPromptAdapter",
    "CLIOutputAdapter",
]
