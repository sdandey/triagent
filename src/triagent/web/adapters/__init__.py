"""Web adapters for unified command system.

These adapters implement the PromptContext and OutputContext protocols
using Chainlit for web rendering.
"""

from triagent.web.adapters.prompt_adapter import ChainlitPromptAdapter
from triagent.web.adapters.output_adapter import ChainlitOutputAdapter

__all__ = [
    "ChainlitPromptAdapter",
    "ChainlitOutputAdapter",
]
