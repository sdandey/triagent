"""Session manager for Chainlit Dynamic Sessions integration."""

import hashlib
import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

from triagent.web.services.session_proxy import SessionProxy

logger = logging.getLogger(__name__)


@dataclass
class SessionCredentials:
    """Credentials for SDK initialization in Dynamic Session."""

    api_provider: str
    api_token: str
    api_base_url: str | None
    team: str


class ChainlitSessionManager:
    """Manages Dynamic Sessions for Chainlit users.

    This class bridges Chainlit's session management with Azure Container Apps
    Dynamic Sessions. It handles:
    - Session ID generation from username
    - SDK initialization in Dynamic Session
    - Message routing to Dynamic Session
    - Azure device flow authentication
    """

    def __init__(self) -> None:
        """Initialize session manager with SessionProxy."""
        self._proxy = SessionProxy()

    @staticmethod
    def generate_session_id(username: str) -> str:
        """Generate deterministic session ID from username.

        Args:
            username: The Chainlit user's identifier.

        Returns:
            16-character hex session ID.
        """
        return hashlib.sha256(username.encode()).hexdigest()[:16]

    async def initialize_session(
        self, session_id: str, credentials: SessionCredentials
    ) -> dict[str, Any]:
        """Initialize SDK in Dynamic Session with credentials.

        This executes Python code in the Dynamic Session to:
        1. Create triagent config directory
        2. Save API credentials
        3. Save team configuration
        4. Set environment variables for non-interactive mode

        Args:
            session_id: The Dynamic Session identifier.
            credentials: API credentials and team info.

        Returns:
            Execution result from Dynamic Session.
        """
        # Escape credentials for Python string interpolation
        api_token_escaped = credentials.api_token.replace("\\", "\\\\").replace(
            '"', '\\"'
        )
        api_base_url_escaped = (credentials.api_base_url or "").replace(
            "\\", "\\\\"
        ).replace('"', '\\"')

        init_code = f'''
import os
from triagent.config import ConfigManager, TriagentConfig, TriagentCredentials

# Configure credentials
config_manager = ConfigManager()
config_manager.ensure_dirs()

creds = TriagentCredentials(
    api_provider="{credentials.api_provider}",
    anthropic_foundry_api_key="{api_token_escaped}",
    anthropic_foundry_base_url="{api_base_url_escaped}",
)
config_manager.save_credentials(creds)

config = TriagentConfig(team="{credentials.team}")
config_manager.save_config(config)

# Set env vars for SDK non-interactive mode
os.environ["CI"] = "true"
os.environ["ANTHROPIC_HEADLESS"] = "1"
os.environ["CLAUDE_CODE_SKIP_ONBOARDING"] = "1"

print("Session initialized")
'''
        logger.info(f"Initializing Dynamic Session {session_id}")
        return await self._proxy.execute_code(session_id, init_code)

    async def send_message(
        self, session_id: str, message: str
    ) -> AsyncGenerator[str, None]:
        """Send message to SDK in Dynamic Session and stream response.

        Args:
            session_id: The Dynamic Session identifier.
            message: User message to send to Claude.

        Yields:
            Response chunks as JSON strings.
        """
        logger.info(f"Sending message to session {session_id}")
        async for chunk in self._proxy.stream_sdk_chat(session_id, message):
            yield chunk

    async def start_azure_device_flow(self, session_id: str) -> dict[str, Any]:
        """Start Azure device code authentication in Dynamic Session.

        This initiates the Azure CLI device code flow inside the Dynamic Session,
        allowing users to authenticate with Azure for MCP tools.

        Args:
            session_id: The Dynamic Session identifier.

        Returns:
            Dict with status and device code message.
        """
        code = '''
import subprocess
import json

result = subprocess.run(
    ["az", "login", "--use-device-code", "--output", "json"],
    capture_output=True,
    text=True,
    timeout=10,  # Quick timeout to get device code
)

if "To sign in" in result.stderr:
    lines = result.stderr.split("\\n")
    for line in lines:
        if "https://microsoft.com/devicelogin" in line:
            print(json.dumps({"status": "pending", "message": line}))
            break
else:
    print(json.dumps({"status": "error", "message": result.stderr}))
'''
        logger.info(f"Starting Azure device flow for session {session_id}")
        return await self._proxy.execute_code(session_id, code)

    async def check_azure_auth(self, session_id: str) -> bool:
        """Check if Azure CLI is authenticated in Dynamic Session.

        Args:
            session_id: The Dynamic Session identifier.

        Returns:
            True if authenticated, False otherwise.
        """
        code = '''
import subprocess

result = subprocess.run(
    ["az", "account", "show", "--output", "json"],
    capture_output=True,
    text=True,
)
print("true" if result.returncode == 0 else "false")
'''
        result = await self._proxy.execute_code(session_id, code)
        stdout = result.get("properties", {}).get("stdout", "")
        return "true" in stdout.lower()

    async def close(self) -> None:
        """Close resources."""
        await self._proxy.close()
