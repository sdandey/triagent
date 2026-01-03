#!/usr/bin/env python3
"""Interactive Azure Container Apps Dynamic Sessions API Testing Script.

Usage:
    python scripts/test-session-api.py

Features:
    - Create and manage sessions
    - Execute Python code in containers
    - Continue conversations (stateful sessions)
    - View session state and variables
"""

import os
import sys
import subprocess
import json
from datetime import datetime

try:
    import httpx
except ImportError:
    print("httpx not installed. Run: pip install httpx")
    sys.exit(1)


class SessionPoolClient:
    """Client for Azure Container Apps Session Pool API."""

    def __init__(self, endpoint: str, az_cmd: str = "az-elevated"):
        """Initialize session pool client.

        Args:
            endpoint: Session pool management endpoint URL.
            az_cmd: Azure CLI command (az or az-elevated).
        """
        self.endpoint = endpoint
        self.az_cmd = az_cmd
        self._token: str | None = None
        self._token_expires: datetime | None = None
        self.current_session_id: str | None = None

    def get_token(self) -> str:
        """Get Azure AD token for dynamicsessions.io scope.

        Returns:
            Access token string.

        Raises:
            RuntimeError: If token acquisition fails.
        """
        result = subprocess.run(
            [
                self.az_cmd,
                "account",
                "get-access-token",
                "--resource",
                "https://dynamicsessions.io",
                "--query",
                "accessToken",
                "-o",
                "tsv",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to get Azure token: {result.stderr}")
        return result.stdout.strip()

    def execute_code(self, code: str, session_id: str | None = None) -> dict:
        """Execute Python code in session container.

        Args:
            code: Python code to execute.
            session_id: Session identifier. If None, uses current session.

        Returns:
            API response with stdout, stderr, status.

        Raises:
            ValueError: If no session ID is set.
        """
        session_id = session_id or self.current_session_id
        if not session_id:
            raise ValueError("No session ID. Create a session first.")

        token = self.get_token()

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.endpoint}/code/execute",
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
            )
            response.raise_for_status()
            return response.json()

    def create_session(self, session_id: str | None = None) -> str:
        """Create a new session by executing init code.

        Args:
            session_id: Optional custom session ID.

        Returns:
            Session ID.
        """
        import secrets

        session_id = session_id or f"test-{secrets.token_hex(8)}"
        self.current_session_id = session_id

        # Initialize session with a simple command
        result = self.execute_code("print('Session initialized')")
        status = result.get("properties", {}).get("status", "Unknown")

        if status == "Succeeded":
            print(f"✓ Session created: {session_id}")
        else:
            print(f"✗ Session creation failed: {status}")

        return session_id

    def upload_file(self, local_path: str, remote_path: str) -> dict:
        """Upload a file to the session container.

        Args:
            local_path: Local file path.
            remote_path: Remote path in container.

        Returns:
            API response.
        """
        with open(local_path, "rb") as f:
            content = f.read()

        # Base64 encode for transfer
        import base64

        encoded = base64.b64encode(content).decode("utf-8")

        code = f"""
import base64
content = base64.b64decode("{encoded}")
with open("{remote_path}", "wb") as f:
    f.write(content)
print(f"Uploaded {{len(content)}} bytes to {remote_path}")
"""
        return self.execute_code(code)


def interactive_mode(client: SessionPoolClient):
    """Run interactive REPL for session testing.

    Args:
        client: SessionPoolClient instance.
    """
    print("\n" + "=" * 60)
    print("Azure Container Apps Dynamic Sessions - Interactive Mode")
    print("=" * 60)
    print("\nCommands:")
    print("  /new [id]     - Create new session (optional custom ID)")
    print("  /session      - Show current session ID")
    print("  /vars         - Show Python variables in session")
    print("  /files        - List files in current directory")
    print("  /upload <local> <remote> - Upload file to session")
    print("  /help         - Show this help")
    print("  /exit         - Exit interactive mode")
    print("  <code>        - Execute Python code")
    print("=" * 60 + "\n")

    while True:
        try:
            prompt = f"[{client.current_session_id or 'no-session'}] >>> "
            user_input = input(prompt).strip()

            if not user_input:
                continue

            if user_input == "/exit":
                print("Goodbye!")
                break

            if user_input == "/help":
                print("\nCommands:")
                print("  /new [id]     - Create new session (optional custom ID)")
                print("  /session      - Show current session ID")
                print("  /vars         - Show Python variables in session")
                print("  /files        - List files in current directory")
                print("  /upload <local> <remote> - Upload file to session")
                print("  /help         - Show this help")
                print("  /exit         - Exit interactive mode")
                print("  <code>        - Execute Python code")
                continue

            if user_input.startswith("/new"):
                parts = user_input.split(maxsplit=1)
                session_id = parts[1] if len(parts) > 1 else None
                client.create_session(session_id)
                continue

            if user_input == "/session":
                print(f"Current session: {client.current_session_id or 'None'}")
                continue

            if user_input == "/vars":
                if not client.current_session_id:
                    print("No active session. Use /new to create one.")
                    continue
                result = client.execute_code(
                    "print([k for k in dir() if not k.startswith('_')])"
                )
                stdout = result.get("properties", {}).get("stdout", "")
                print(f"Variables: {stdout.strip()}")
                continue

            if user_input == "/files":
                if not client.current_session_id:
                    print("No active session. Use /new to create one.")
                    continue
                result = client.execute_code("import os; print(os.listdir('.'))")
                stdout = result.get("properties", {}).get("stdout", "")
                print(f"Files: {stdout.strip()}")
                continue

            if user_input.startswith("/upload"):
                parts = user_input.split()
                if len(parts) != 3:
                    print("Usage: /upload <local_path> <remote_path>")
                    continue
                _, local_path, remote_path = parts
                if not os.path.exists(local_path):
                    print(f"File not found: {local_path}")
                    continue
                if not client.current_session_id:
                    print("No active session. Use /new to create one.")
                    continue
                result = client.upload_file(local_path, remote_path)
                stdout = result.get("properties", {}).get("stdout", "")
                print(stdout.strip())
                continue

            # Execute as Python code
            if not client.current_session_id:
                print("No active session. Creating one...")
                client.create_session()

            result = client.execute_code(user_input)
            props = result.get("properties", {})

            stdout = props.get("stdout", "")
            stderr = props.get("stderr", "")
            status = props.get("status", "Unknown")

            if stdout:
                print(stdout, end="" if stdout.endswith("\n") else "\n")
            if stderr:
                print(f"[stderr] {stderr}", end="" if stderr.endswith("\n") else "\n")
            if status != "Succeeded":
                print(f"[status: {status}]")

        except KeyboardInterrupt:
            print("\nUse /exit to quit.")
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point."""
    # Get endpoint from environment or prompt
    endpoint = os.environ.get("TRIAGENT_SESSION_POOL_ENDPOINT")
    if not endpoint:
        print("TRIAGENT_SESSION_POOL_ENDPOINT not set.")
        print("Get it with: az-elevated containerapp sessionpool show \\")
        print("  --name triagent-sandbox-session-pool \\")
        print("  --resource-group triagent-sandbox-rg \\")
        print("  --query 'properties.poolManagementEndpoint' -o tsv")
        print()
        print("Or run via the wrapper script: ./scripts/test-session-api.sh")
        sys.exit(1)

    az_cmd = os.environ.get("AZ_CMD", "az-elevated")
    client = SessionPoolClient(endpoint, az_cmd)

    # Verify Azure authentication
    print(f"Using Azure CLI: {az_cmd}")
    try:
        client.get_token()
        print("✓ Azure authentication verified")
    except RuntimeError as e:
        print(f"✗ Azure authentication failed: {e}")
        print(f"Run: {az_cmd} login")
        sys.exit(1)

    interactive_mode(client)


if __name__ == "__main__":
    main()
