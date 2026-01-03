"""Azure Container Apps Session Pool proxy for Triagent Web API."""

import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx
from azure.identity.aio import DefaultAzureCredential

from triagent.web.config import WebConfig


class SessionProxy:
    """Proxy requests to Azure Container Apps Session Pool."""

    def __init__(self) -> None:
        """Initialize session proxy."""
        self.config = WebConfig()
        self._credential: DefaultAzureCredential | None = None

    async def get_access_token(self) -> str:
        """Get token for dynamicsessions.io scope.

        Returns:
            Access token string.
        """
        if self._credential is None:
            self._credential = DefaultAzureCredential()
        token = await self._credential.get_token(
            "https://dynamicsessions.io/.default"
        )
        return token.token

    async def execute_code(self, session_id: str, code: str) -> dict[str, Any]:
        """Execute code in session container.

        Args:
            session_id: Session identifier.
            code: Python code to execute.

        Returns:
            Execution result from session pool.
        """
        token = await self.get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.session_pool_endpoint}/code/execute",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Identifier": session_id,
                    "Content-Type": "application/json",
                },
                json={
                    "properties": {
                        "codeInputType": "inline",
                        "executionType": "synchronous",
                        "code": code,
                    }
                },
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()

    async def proxy_request(
        self,
        session_id: str,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generic proxy to container internal API.

        Args:
            session_id: Session identifier.
            method: HTTP method (GET, POST, etc.).
            path: API path.
            json_data: Optional JSON body.

        Returns:
            Response from container API.
        """
        # Execute Python code that makes HTTP request inside container
        code = f'''
import requests
import json
response = requests.{method.lower()}(
    "http://localhost:8081{path}",
    json={json.dumps(json_data) if json_data else None},
    timeout=30,
)
print(json.dumps({{"status": response.status_code, "data": response.json()}}))
'''
        result = await self.execute_code(session_id, code)
        return result

    async def stream_chat(
        self,
        session_id: str,
        message: str,
    ) -> AsyncGenerator[str, None]:
        """Stream chat response from container.

        Args:
            session_id: Session identifier.
            message: Chat message to send.

        Yields:
            SSE event strings.
        """
        token = await self.get_access_token()

        # Escape message for inclusion in Python code
        escaped_message = message.replace("\\", "\\\\").replace('"', '\\"')

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.config.session_pool_endpoint}/code/execute",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Identifier": session_id,
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
                json={
                    "properties": {
                        "codeInputType": "inline",
                        "executionType": "synchronous",
                        "code": f'await handle_chat_message("{escaped_message}")',
                    }
                },
                timeout=120.0,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        yield line

    async def stream_sdk_chat(
        self,
        session_id: str,
        message: str,
    ) -> AsyncGenerator[str, None]:
        """Stream SDK chat response from Dynamic Session.

        This executes the full Claude SDK chat flow inside the Dynamic Session
        and streams the response back. The SDK is initialized with credentials
        saved by ChainlitSessionManager.initialize_session().

        Args:
            session_id: Session identifier.
            message: User message to send to Claude SDK.

        Yields:
            Response chunks as JSON strings with type and content.
        """
        token = await self.get_access_token()

        # Escape message for Python string
        escaped = (
            message.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
        )

        # Python code to run SDK chat in Dynamic Session
        sdk_code = f'''
import asyncio
import json
import sys
from claude_agent_sdk import ClaudeSDKClient
from rich.console import Console
from triagent.sdk_client import create_sdk_client
from triagent.config import ConfigManager

async def run_chat():
    try:
        config_manager = ConfigManager()
        console = Console(force_terminal=False, no_color=True)
        client_factory = create_sdk_client(config_manager, console)
        options = client_factory._build_options()

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt="{escaped}")
            async for msg in client.receive_response():
                msg_type = type(msg).__name__
                if msg_type == "AssistantMessage":
                    for block in msg.content:
                        block_type = type(block).__name__
                        if block_type == "TextBlock":
                            print(json.dumps({{"type": "text", "content": block.text}}))
                            sys.stdout.flush()
                        elif block_type == "ToolUseBlock":
                            print(json.dumps({{"type": "tool", "name": block.name, "input": str(block.input)}}))
                            sys.stdout.flush()
    except Exception as e:
        print(json.dumps({{"type": "error", "content": str(e)}}))
        sys.stdout.flush()

asyncio.run(run_chat())
'''

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.config.session_pool_endpoint}/code/execute",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Identifier": session_id,
                    "Content-Type": "application/json",
                },
                json={
                    "properties": {
                        "codeInputType": "inline",
                        "executionType": "synchronous",
                        "code": sdk_code,
                    }
                },
                timeout=300.0,  # 5 min timeout for long SDK responses
            ) as response:
                async for line in response.aiter_lines():
                    if line.strip():
                        yield line

    async def close(self) -> None:
        """Close credential resources."""
        if self._credential is not None:
            await self._credential.close()
