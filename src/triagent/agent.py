"""Azure AI Foundry client for Triagent CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from triagent.config import TriagentCredentials

if TYPE_CHECKING:
    from triagent.tools.error_recovery import ErrorContext


class AzureFoundryClient:
    """Custom client for Azure AI Foundry Claude API."""

    def __init__(self, credentials: TriagentCredentials) -> None:
        """Initialize Azure Foundry client.

        Args:
            credentials: Triagent credentials with Azure Foundry config
        """
        self.base_url = credentials.anthropic_foundry_base_url
        self.model = credentials.anthropic_foundry_model
        self.api_key = credentials.anthropic_foundry_api_key

    def send_message(
        self,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> dict:
        """Send a message to Azure Foundry Claude endpoint.

        Args:
            messages: List of message dicts with role and content
            system: Optional system prompt
            max_tokens: Maximum tokens to generate
            tools: Optional list of tool definitions

        Returns:
            Full response dictionary from the API (Anthropic format)
        """
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        # Build request body (Anthropic format)
        body: dict = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        # Add system prompt if provided
        if system:
            body["system"] = system

        # Add tools if provided (Anthropic format)
        if tools:
            body["tools"] = tools

        response = httpx.post(self.base_url, headers=headers, json=body, timeout=120)
        response.raise_for_status()

        return response.json()

    def send_message_with_error_info(
        self,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> tuple[dict | None, ErrorContext | None]:
        """Send a message and return detailed error info if failed.

        Args:
            messages: List of message dicts with role and content
            system: Optional system prompt
            max_tokens: Maximum tokens to generate
            tools: Optional list of tool definitions

        Returns:
            Tuple of (response_dict, error_context)
            - On success: (response, None)
            - On error: (None, ErrorContext)
        """
        from triagent.tools.error_recovery import ErrorContext, classify_http_error

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        body: dict = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        if system:
            body["system"] = system

        if tools:
            body["tools"] = tools

        try:
            response = httpx.post(self.base_url, headers=headers, json=body, timeout=120)
            response.raise_for_status()
            return response.json(), None
        except httpx.HTTPStatusError as e:
            error_type = classify_http_error(e.response.status_code, e.response.text)
            return None, ErrorContext(
                status_code=e.response.status_code,
                error_message=e.response.text,
                error_type=error_type,
            )

    def extract_text(self, response: dict) -> str:
        """Extract text content from Anthropic-style response.

        Args:
            response: The API response dictionary

        Returns:
            The text content from the response
        """
        content = response.get("content", [])
        text_parts = []
        for block in content:
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        return "".join(text_parts)

    def has_tool_calls(self, response: dict) -> bool:
        """Check if the response contains tool calls.

        Args:
            response: The API response dictionary

        Returns:
            True if there are tool calls to process
        """
        content = response.get("content", [])
        for block in content:
            if block.get("type") == "tool_use":
                return True
        return False

    def get_tool_calls(self, response: dict) -> list[dict]:
        """Extract tool calls from the response.

        Args:
            response: The API response dictionary

        Returns:
            List of tool call dictionaries with id, name, and arguments
        """
        tool_calls = []
        content = response.get("content", [])
        for block in content:
            if block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block.get("id", ""),
                    "name": block.get("name", ""),
                    "arguments": block.get("input", {}),
                })
        return tool_calls
