"""Chainlit output adapter for web rendering.

This adapter implements the OutputContext protocol for Chainlit web environments,
using Chainlit messages for output rendering.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ChainlitOutputAdapter:
    """Chainlit UI output implementation for Web.

    Implements the OutputContext protocol for web-based output rendering
    using Chainlit messages.
    """

    def __init__(self):
        """Initialize the Chainlit output adapter."""
        pass

    async def write_text(self, text: str) -> None:
        """Write plain text output.

        Args:
            text: The text to display.
        """
        try:
            import chainlit as cl

            await cl.Message(content=text).send()

        except ImportError:
            logger.error("Chainlit not available")
        except Exception as e:
            logger.error(f"Error in write_text: {e}")

    async def write_markdown(self, markdown: str) -> None:
        """Write markdown-formatted output.

        Args:
            markdown: Markdown content to render.
        """
        try:
            import chainlit as cl

            # Chainlit natively supports markdown
            await cl.Message(content=markdown).send()

        except ImportError:
            logger.error("Chainlit not available")
        except Exception as e:
            logger.error(f"Error in write_markdown: {e}")

    async def show_table(
        self,
        headers: list[str],
        rows: list[list[str]],
        title: str | None = None,
    ) -> None:
        """Display a table as markdown.

        Args:
            headers: Column headers.
            rows: Table rows (list of lists).
            title: Optional table title.
        """
        try:
            import chainlit as cl

            # Build markdown table
            md_lines = []

            if title:
                md_lines.append(f"**{title}**\n")

            # Header row
            md_lines.append("| " + " | ".join(headers) + " |")

            # Separator row
            md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

            # Data rows
            for row in rows:
                # Convert status values to emoji for better display
                styled_row = []
                for cell in row:
                    if cell in ("OK", "✓"):
                        styled_row.append("✅")
                    elif cell in ("Not found", "Missing"):
                        styled_row.append("⚠️")
                    elif cell in ("Error", "Failed", "✗"):
                        styled_row.append("❌")
                    else:
                        styled_row.append(str(cell))
                md_lines.append("| " + " | ".join(styled_row) + " |")

            await cl.Message(content="\n".join(md_lines)).send()

        except ImportError:
            logger.error("Chainlit not available")
        except Exception as e:
            logger.error(f"Error in show_table: {e}")

    async def show_panel(
        self,
        content: str,
        title: str | None = None,
        style: str = "info",
    ) -> None:
        """Display a panel/card with content using blockquote styling.

        Args:
            content: Panel content (can be markdown).
            title: Optional panel title.
            style: One of "info", "success", "warning", "error".
        """
        try:
            import chainlit as cl

            # Add emoji based on style
            emoji_map = {
                "info": "ℹ️",
                "success": "✅",
                "warning": "⚠️",
                "error": "❌",
            }
            emoji = emoji_map.get(style, "")

            # Build blockquote-style panel
            lines = []
            if title:
                lines.append(f"> {emoji} **{title}**")
                lines.append(">")

            # Add content lines with blockquote prefix
            for line in content.split("\n"):
                lines.append(f"> {line}")

            await cl.Message(content="\n".join(lines)).send()

        except ImportError:
            logger.error("Chainlit not available")
        except Exception as e:
            logger.error(f"Error in show_panel: {e}")

    async def show_key_value(
        self,
        items: list[tuple[str, str]],
        title: str | None = None,
    ) -> None:
        """Display key-value pairs as a list.

        Args:
            items: List of (key, value) tuples.
            title: Optional section title.
        """
        try:
            import chainlit as cl

            lines = []

            if title:
                lines.append(f"**{title}**\n")

            for key, value in items:
                # Style certain values
                if value in ("enabled", "true", "yes"):
                    display_value = f"✅ {value}"
                elif value in ("disabled", "false", "no"):
                    display_value = f"❌ {value}"
                elif value == "not set":
                    display_value = f"*{value}*"
                elif value.startswith("***"):
                    display_value = f"`{value}`"
                else:
                    display_value = value

                lines.append(f"- **{key}:** {display_value}")

            await cl.Message(content="\n".join(lines)).send()

        except ImportError:
            logger.error("Chainlit not available")
        except Exception as e:
            logger.error(f"Error in show_key_value: {e}")
