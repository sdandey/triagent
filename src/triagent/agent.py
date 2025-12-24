"""Claude Agent SDK integration for Triagent CLI."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field

import anthropic
import httpx
from anthropic import Anthropic
from anthropic.types import Message, TextBlock

from triagent.config import ConfigManager, TriagentCredentials
from triagent.prompts.system import get_system_prompt


def _get_databricks_token(host: str) -> str | None:
    """Get fresh OAuth token from Databricks CLI.

    Args:
        host: Databricks workspace host URL

    Returns:
        Access token or None if failed
    """
    try:
        result = subprocess.run(
            ["databricks", "auth", "token", "--host", host],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            token_data = json.loads(result.stdout)
            return token_data.get("access_token")
        return None
    except Exception:
        return None


class DatabricksClient:
    """Custom client for Databricks Foundation Model API."""

    def __init__(self, credentials: TriagentCredentials) -> None:
        """Initialize Databricks client.

        Args:
            credentials: Triagent credentials with Databricks config
        """
        self.base_url = credentials.databricks_base_url
        self.model = credentials.databricks_model
        self.static_token = credentials.databricks_auth_token

        # Extract host from base_url for token refresh
        # base_url format: https://adb-xxx.azuredatabricks.net/serving-endpoints/model-name
        parts = self.base_url.split("/serving-endpoints/")
        self.host = parts[0] if parts else self.base_url

    def _get_token(self) -> str:
        """Get a valid token, preferring fresh OAuth token."""
        # Try to get fresh token from Databricks CLI
        token = _get_databricks_token(self.host)
        if token:
            return token
        # Fall back to static token
        return self.static_token

    def _get_endpoint_url(self) -> str:
        """Get the full endpoint URL for invocations."""
        if self.base_url.endswith("/invocations"):
            return self.base_url
        return f"{self.base_url}/invocations"

    def send_message(
        self,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> dict:
        """Send a message to Databricks Claude endpoint.

        Args:
            messages: List of message dicts with role and content
            system: Optional system prompt
            max_tokens: Maximum tokens to generate
            tools: Optional list of tool definitions (OpenAI function format)

        Returns:
            Full response dictionary from the API
        """
        token = self._get_token()
        url = self._get_endpoint_url()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # Build request body (OpenAI-compatible format for Databricks)
        body: dict = {
            "messages": messages,
            "max_tokens": max_tokens,
        }

        # Add system message if provided
        if system:
            body["messages"] = [{"role": "system", "content": system}] + messages

        # Add tools if provided (OpenAI function calling format)
        if tools:
            body["tools"] = [
                {"type": "function", "function": tool} for tool in tools
            ]

        response = httpx.post(url, headers=headers, json=body, timeout=120)
        response.raise_for_status()

        return response.json()

    def send_message_with_error_info(
        self,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> tuple[dict | None, "ErrorContext | None"]:
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

        token = self._get_token()
        url = self._get_endpoint_url()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        body: dict = {
            "messages": messages,
            "max_tokens": max_tokens,
        }

        if system:
            body["messages"] = [{"role": "system", "content": system}] + messages

        if tools:
            body["tools"] = [
                {"type": "function", "function": tool} for tool in tools
            ]

        try:
            response = httpx.post(url, headers=headers, json=body, timeout=120)
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
        """Extract text content from OpenAI-style response.

        Args:
            response: The API response dictionary

        Returns:
            The text content from the response
        """
        if "choices" in response and len(response["choices"]) > 0:
            message = response["choices"][0].get("message", {})
            return message.get("content", "") or ""
        return ""

    def has_tool_calls(self, response: dict) -> bool:
        """Check if the response contains tool calls.

        Args:
            response: The API response dictionary

        Returns:
            True if there are tool calls to process
        """
        if "choices" in response and len(response["choices"]) > 0:
            message = response["choices"][0].get("message", {})
            tool_calls = message.get("tool_calls", [])
            return len(tool_calls) > 0
        return False

    def get_tool_calls(self, response: dict) -> list[dict]:
        """Extract tool calls from the response.

        Args:
            response: The API response dictionary

        Returns:
            List of tool call dictionaries with id, name, and arguments
        """
        tool_calls = []
        if "choices" in response and len(response["choices"]) > 0:
            message = response["choices"][0].get("message", {})
            for tc in message.get("tool_calls", []):
                tool_calls.append({
                    "id": tc.get("id", ""),
                    "name": tc.get("function", {}).get("name", ""),
                    "arguments": json.loads(tc.get("function", {}).get("arguments", "{}")),
                })
        return tool_calls


@dataclass
class ConversationMessage:
    """A message in the conversation history."""

    role: str  # "user" or "assistant"
    content: str


@dataclass
class AgentSession:
    """Manages a conversation session with Claude."""

    config_manager: ConfigManager
    team: str
    model: str = "claude-sonnet-4-20250514"
    messages: list[ConversationMessage] = field(default_factory=list)
    _client: Anthropic | None = None
    _databricks_client: DatabricksClient | None = None
    _model_override: str | None = None
    _use_databricks: bool = False

    def __post_init__(self) -> None:
        """Initialize the client."""
        self._setup_client()

    def _setup_client(self) -> None:
        """Set up the client based on configured provider."""
        credentials = self.config_manager.load_credentials()

        if credentials.api_provider == "databricks":
            # Use custom Databricks client
            self._use_databricks = True
            self._databricks_client = DatabricksClient(credentials)
            self._model_override = credentials.databricks_model
        elif credentials.api_provider == "azure_foundry" and credentials.anthropic_foundry_api_key:
            # Azure Foundry uses environment variables
            os.environ["CLAUDE_CODE_USE_FOUNDRY"] = "1"
            os.environ["ANTHROPIC_FOUNDRY_API_KEY"] = credentials.anthropic_foundry_api_key
            os.environ["ANTHROPIC_FOUNDRY_RESOURCE"] = credentials.anthropic_foundry_resource
            self._client = Anthropic()
        else:
            # Default: Direct Anthropic API
            self._client = Anthropic()

    @property
    def client(self) -> Anthropic:
        """Get or create the Anthropic client."""
        if self._client is None and not self._use_databricks:
            self._setup_client()
        return self._client  # type: ignore

    @property
    def effective_model(self) -> str:
        """Get the effective model to use (may be overridden by provider)."""
        return self._model_override or self.model

    @property
    def system_prompt(self) -> str:
        """Get the system prompt for the current team."""
        return get_system_prompt(self.team)

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation history."""
        self.messages.append(ConversationMessage(role="user", content=content))

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the conversation history."""
        self.messages.append(ConversationMessage(role="assistant", content=content))

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.messages.clear()

    def get_messages_for_api(self) -> list[dict[str, str]]:
        """Convert conversation history to API format."""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]

    def send_message(self, user_message: str) -> str:
        """Send a message and get a response.

        Args:
            user_message: The user's message

        Returns:
            The assistant's response text
        """
        self.add_user_message(user_message)

        try:
            if self._use_databricks and self._databricks_client:
                # Use custom Databricks client
                response = self._databricks_client.send_message(
                    messages=self.get_messages_for_api(),
                    system=self.system_prompt,
                    max_tokens=4096,
                )
                response_text = self._databricks_client.extract_text(response)
            else:
                # Use Anthropic SDK
                response = self.client.messages.create(
                    model=self.effective_model,
                    max_tokens=4096,
                    system=self.system_prompt,
                    messages=self.get_messages_for_api(),
                )
                response_text = self._extract_text(response)

            self.add_assistant_message(response_text)
            return response_text

        except anthropic.APIConnectionError as e:
            error_msg = f"Connection error: {e}"
            return f"[Error] {error_msg}"
        except anthropic.RateLimitError as e:
            error_msg = f"Rate limit exceeded: {e}"
            return f"[Error] {error_msg}"
        except anthropic.APIStatusError as e:
            error_msg = f"API error: {e.message}"
            return f"[Error] {error_msg}"
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error: {e.response.status_code} - {e.response.text}"
            return f"[Error] {error_msg}"
        except Exception as e:
            return f"[Error] {e}"

    def stream_message(self, user_message: str):
        """Stream a message response.

        Args:
            user_message: The user's message

        Yields:
            Text chunks as they arrive
        """
        self.add_user_message(user_message)
        full_response = ""

        try:
            if self._use_databricks and self._databricks_client:
                # Databricks doesn't support streaming, yield entire response
                response = self._databricks_client.send_message(
                    messages=self.get_messages_for_api(),
                    system=self.system_prompt,
                    max_tokens=4096,
                )
                response_text = self._databricks_client.extract_text(response)
                self.add_assistant_message(response_text)
                yield response_text
            else:
                # Use Anthropic SDK streaming
                with self.client.messages.stream(
                    model=self.effective_model,
                    max_tokens=4096,
                    system=self.system_prompt,
                    messages=self.get_messages_for_api(),
                ) as stream:
                    for text in stream.text_stream:
                        full_response += text
                        yield text

                self.add_assistant_message(full_response)

        except Exception as e:
            error_msg = f"[Error] {e}"
            yield error_msg

    def send_message_with_tools(
        self,
        user_message: str,
        confirm_callback: Callable[[str], bool] | None = None,
        on_tool_start: Callable[[str, str], None] | None = None,
        on_tool_end: Callable[[str, bool], None] | None = None,
        on_retry: Callable[[int], None] | None = None,
    ):
        """Send a message and handle tool calls with intelligent error recovery.

        Args:
            user_message: The user's message
            confirm_callback: Function to ask user for confirmation on write operations.
                            Takes the command string, returns True to proceed.
            on_tool_start: Callback when tool execution starts (tool_name, command)
            on_tool_end: Callback when tool execution ends (tool_name, success)
            on_retry: Callback when retrying after error (attempt_number)

        Yields:
            Text chunks and tool execution events
        """
        from triagent.tools.azure_cli import AZURE_CLI_TOOL, execute_azure_cli
        from triagent.tools.error_recovery import (
            ErrorType,
            RetryConfig,
            extract_command_base,
            generate_recovery_instruction,
            get_cli_help,
            truncate_aggressively,
        )

        retry_config = RetryConfig()

        self.add_user_message(user_message)

        # Build messages list for API (includes tool results)
        api_messages = self.get_messages_for_api()

        # Track for retry
        last_command: str | None = None
        last_output: str | None = None
        attempt = 0

        # Tool use loop - keep calling until no more tool calls
        while True:
            attempt += 1

            try:
                if self._use_databricks and self._databricks_client:
                    # Use error-aware method for retry logic
                    response, error_ctx = self._databricks_client.send_message_with_error_info(
                        messages=api_messages,
                        system=self.system_prompt,
                        max_tokens=4096,
                        tools=[AZURE_CLI_TOOL],
                    )

                    # Handle API error with potential retry
                    if error_ctx is not None:
                        if (
                            error_ctx.error_type == ErrorType.CONTEXT_TOO_LARGE
                            and attempt <= retry_config.max_attempts
                        ):
                            # Notify retry
                            if on_retry:
                                on_retry(attempt)

                            # Prepare recovery context
                            error_ctx.attempt_number = attempt
                            error_ctx.original_command = last_command
                            error_ctx.previous_output = last_output

                            # Fetch CLI help if available
                            help_text = None
                            if retry_config.enable_help_lookup and last_command:
                                cmd_base = extract_command_base(last_command)
                                help_text = get_cli_help(cmd_base)

                            # Generate recovery instruction
                            recovery_msg = generate_recovery_instruction(error_ctx, help_text)

                            # Add recovery instruction to messages
                            api_messages.append({
                                "role": "user",
                                "content": recovery_msg,
                            })

                            # Continue loop to retry
                            continue

                        # Non-recoverable error or max retries exceeded
                        error_snippet = error_ctx.error_message[:300] if error_ctx.error_message else "Unknown error"
                        yield f"[Error] API returned {error_ctx.status_code}: {error_snippet}"
                        return

                    # Success path - process response
                    if self._databricks_client.has_tool_calls(response):
                        tool_calls = self._databricks_client.get_tool_calls(response)

                        # Add assistant message with tool calls to conversation
                        assistant_msg = response["choices"][0]["message"]
                        api_messages.append(assistant_msg)

                        # Execute each tool call
                        for tool_call in tool_calls:
                            tool_name = tool_call["name"]
                            tool_id = tool_call["id"]

                            if tool_name == "execute_azure_cli":
                                command = tool_call["arguments"].get("command", "")
                                last_command = command  # Track for retry

                                # Notify tool start
                                if on_tool_start:
                                    on_tool_start(tool_name, command)

                                # Execute the command
                                result = execute_azure_cli(
                                    command,
                                    confirm_callback=confirm_callback,
                                )

                                # Notify tool end
                                if on_tool_end:
                                    on_tool_end(tool_name, result["success"])

                                # Add tool result to messages (truncate if too long)
                                tool_result_content = (
                                    result["output"] if result["success"]
                                    else f"Error: {result['error']}"
                                )
                                last_output = tool_result_content  # Track for retry

                                # Adaptive truncation based on attempt number
                                max_output_len = 4000 if attempt == 1 else retry_config.aggressive_truncation_threshold
                                if len(tool_result_content) > max_output_len:
                                    tool_result_content = truncate_aggressively(
                                        tool_result_content, max_output_len
                                    )

                                api_messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_id,
                                    "content": tool_result_content,
                                })

                        # Reset attempt counter on successful tool execution
                        attempt = 0
                        # Continue loop to get next response
                        continue

                    # No tool calls - extract final text
                    response_text = self._databricks_client.extract_text(response)
                    self.add_assistant_message(response_text)
                    yield response_text
                    return

                else:
                    # Non-Databricks path - just use regular send for now
                    response = self.client.messages.create(
                        model=self.effective_model,
                        max_tokens=4096,
                        system=self.system_prompt,
                        messages=self.get_messages_for_api(),
                    )
                    response_text = self._extract_text(response)
                    self.add_assistant_message(response_text)
                    yield response_text
                    return

            except Exception as e:
                yield f"[Error] {e}"
                return

    def _extract_text(self, response: Message) -> str:
        """Extract text content from a response.

        Args:
            response: The API response

        Returns:
            Concatenated text from all text blocks
        """
        text_parts = []
        for block in response.content:
            if isinstance(block, TextBlock):
                text_parts.append(block.text)
        return "".join(text_parts)


def create_agent_session(
    config_manager: ConfigManager,
    team: str | None = None,
) -> AgentSession:
    """Create a new agent session.

    Args:
        config_manager: Config manager instance
        team: Team name (uses config default if not specified)

    Returns:
        Configured AgentSession
    """
    if team is None:
        config = config_manager.load_config()
        team = config.team

    return AgentSession(config_manager=config_manager, team=team)
