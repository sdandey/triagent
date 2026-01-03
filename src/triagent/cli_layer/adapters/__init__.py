"""CLI adapters for unified command system.

These adapters implement the PromptContext and OutputContext protocols
using Rich for terminal rendering.
"""

from triagent.cli_layer.adapters.prompt_adapter import CLIPromptAdapter
from triagent.cli_layer.adapters.output_adapter import CLIOutputAdapter

__all__ = [
    "CLIPromptAdapter",
    "CLIOutputAdapter",
]
