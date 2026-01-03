"""Chainlit prompt adapter for web prompts.

This adapter implements the PromptContext protocol for Chainlit web environments,
using Chainlit actions and user messages for interactive prompts.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ChainlitPromptAdapter:
    """Chainlit UI prompt implementation for Web.

    Implements the PromptContext protocol for web-based user interaction
    using Chainlit's action messages and user prompts.
    """

    def __init__(self, timeout: int = 300):
        """Initialize the Chainlit prompt adapter.

        Args:
            timeout: Timeout in seconds for user prompts.
        """
        self.timeout = timeout

    async def ask_selection(
        self,
        prompt: str,
        options: list[tuple[str, str]],
        default: int = 0,
    ) -> str | None:
        """Ask user to select from a list of options using Chainlit actions.

        Args:
            prompt: The question to display.
            options: List of (value, display_label) tuples.
            default: Index of default option (0-based).

        Returns:
            Selected value, or None if cancelled/timeout.
        """
        try:
            import chainlit as cl

            # Build action buttons
            actions = [
                cl.Action(
                    name=value,
                    payload={"value": value, "index": i},
                    label=display,
                )
                for i, (value, display) in enumerate(options)
            ]

            response = await cl.AskActionMessage(
                content=prompt,
                actions=actions,
                timeout=self.timeout,
            ).send()

            if response is None:
                logger.debug("Selection cancelled or timed out")
                return options[default][0] if options else None

            # Return the selected value
            return response.get("name")

        except ImportError:
            logger.error("Chainlit not available")
            return options[default][0] if options else None
        except Exception as e:
            logger.error(f"Error in ask_selection: {e}")
            return options[default][0] if options else None

    async def ask_text(
        self,
        prompt: str,
        secret: bool = False,
        default: str | None = None,
    ) -> str | None:
        """Ask user for text input using Chainlit user message.

        Args:
            prompt: The question to display.
            secret: If True, indicate this is sensitive (note: Chainlit doesn't hide input).
            default: Default value if user provides empty input.

        Returns:
            User input, or None if cancelled/timeout.
        """
        try:
            import chainlit as cl

            # Build prompt text
            display_prompt = prompt
            if secret:
                display_prompt += "\n\n*Note: Input will be visible in chat history.*"
            if default:
                display_prompt += f"\n\n*Default: {default}*"

            response = await cl.AskUserMessage(
                content=display_prompt,
                timeout=self.timeout,
            ).send()

            if response is None:
                logger.debug("Text input cancelled or timed out")
                return default

            # Extract the user's response
            value = str(response.get("output", "")).strip()
            return value if value else default

        except ImportError:
            logger.error("Chainlit not available")
            return default
        except Exception as e:
            logger.error(f"Error in ask_text: {e}")
            return default

    async def ask_confirmation(
        self,
        message: str,
        default: bool = True,
    ) -> bool:
        """Ask user for yes/no confirmation using Chainlit action buttons.

        Args:
            message: The confirmation message.
            default: Default response if timeout/cancelled.

        Returns:
            True if confirmed, False otherwise.
        """
        try:
            import chainlit as cl

            actions = [
                cl.Action(
                    name="yes",
                    payload={"confirmed": True},
                    label="Yes",
                ),
                cl.Action(
                    name="no",
                    payload={"confirmed": False},
                    label="No",
                ),
            ]

            response = await cl.AskActionMessage(
                content=message,
                actions=actions,
                timeout=self.timeout,
            ).send()

            if response is None:
                logger.debug("Confirmation cancelled or timed out")
                return default

            return response.get("name") == "yes"

        except ImportError:
            logger.error("Chainlit not available")
            return default
        except Exception as e:
            logger.error(f"Error in ask_confirmation: {e}")
            return default

    async def display_message(
        self,
        message: str,
        style: str = "info",
    ) -> None:
        """Display a styled message to the user.

        Args:
            message: The message to display.
            style: One of "info", "success", "warning", "error".
        """
        try:
            import chainlit as cl

            # Add emoji prefix based on style
            prefix_map = {
                "info": "ℹ️",
                "success": "✅",
                "warning": "⚠️",
                "error": "❌",
            }
            prefix = prefix_map.get(style, "•")

            await cl.Message(content=f"{prefix} {message}").send()

        except ImportError:
            logger.error("Chainlit not available")
        except Exception as e:
            logger.error(f"Error in display_message: {e}")

    async def display_progress(
        self,
        message: str,
    ) -> None:
        """Display a progress/loading message.

        Args:
            message: The progress message (e.g., "Loading...").
        """
        try:
            import chainlit as cl

            await cl.Message(content=f"*{message}...*").send()

        except ImportError:
            logger.error("Chainlit not available")
        except Exception as e:
            logger.error(f"Error in display_progress: {e}")
