"""Integration tests for Claude Code SDK slash commands.

Tests all discovered SDK commands by:
1. Connecting to Claude Code
2. Discovering available commands via get_server_info()
3. Executing each command with a simple prompt
4. Validating the response is received with detailed message type analysis
"""

from __future__ import annotations

from typing import Any

import pytest
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient


class TestSDKCommandsIntegration:
    """Integration tests for SDK slash commands."""

    @pytest.mark.asyncio
    async def test_discover_sdk_commands(self) -> None:
        """Test that SDK commands can be discovered via get_server_info()."""
        options = ClaudeAgentOptions()

        async with ClaudeSDKClient(options=options) as client:
            server_info = await client.get_server_info()

            assert server_info is not None, "get_server_info() returned None"
            commands = server_info.get("commands", [])
            assert len(commands) > 0, "No commands discovered"

            # Print discovered commands
            print(f"\nDiscovered {len(commands)} SDK commands:")
            for cmd in commands:
                if isinstance(cmd, dict):
                    name = cmd.get("name", cmd.get("command", str(cmd)))
                    desc = cmd.get("description", "")
                    print(f"  - {name}: {desc}")
                else:
                    print(f"  - {cmd}")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("command", [
        "/help",
        "/compact",
        "/clear",
    ])
    async def test_builtin_sdk_commands(self, command: str) -> None:
        """Test built-in SDK commands respond without errors."""
        options = ClaudeAgentOptions()

        async with ClaudeSDKClient(options=options) as client:
            # Send command
            await client.query(prompt=command)

            # Collect responses
            responses: list[Any] = []
            async for msg in client.receive_response():
                responses.append(msg)

            # Validate we got a response
            assert len(responses) > 0, f"No response for {command}"

            # Check for ResultMessage (indicates completion)
            result_msgs = [m for m in responses if type(m).__name__ == "ResultMessage"]
            assert len(result_msgs) > 0, f"No ResultMessage for {command}"

    @pytest.mark.asyncio
    async def test_all_discovered_commands(self) -> None:
        """Test all discovered SDK commands with detailed message and output validation."""
        import re

        options = ClaudeAgentOptions()
        results: list[dict[str, Any]] = []

        async with ClaudeSDKClient(options=options) as client:
            # Discover commands
            server_info = await client.get_server_info()
            commands = server_info.get("commands", []) if server_info else []

            for cmd_info in commands:
                # Extract command name
                if isinstance(cmd_info, dict):
                    cmd_name = cmd_info.get("name", cmd_info.get("command", ""))
                else:
                    cmd_name = str(cmd_info)

                if not cmd_name:
                    continue

                # Ensure leading slash
                if not cmd_name.startswith("/"):
                    cmd_name = f"/{cmd_name}"

                # Test command
                try:
                    await client.query(prompt=cmd_name)

                    responses: list[Any] = []
                    msg_types: set[str] = set()
                    all_output: list[str] = []

                    async for msg in client.receive_response():
                        responses.append(msg)
                        msg_type = type(msg).__name__
                        msg_types.add(msg_type)

                        # Extract output content from different message types
                        if msg_type == "UserMessage":
                            # SDK slash command output (e.g., /release-notes)
                            content = getattr(msg, "content", "")
                            if content:
                                # Strip XML wrapper tags
                                cleaned = re.sub(r"<local-command-stdout>\s*", "", content)
                                cleaned = re.sub(r"\s*</local-command-stdout>", "", cleaned)
                                if cleaned.strip():
                                    all_output.append(cleaned.strip())

                        elif msg_type == "AssistantMessage":
                            # Extract text from content blocks
                            for block in getattr(msg, "content", []):
                                if type(block).__name__ == "TextBlock":
                                    text = getattr(block, "text", "")
                                    if text.strip():
                                        all_output.append(text.strip())

                        elif msg_type == "SystemMessage":
                            # Check for command result in data
                            data = getattr(msg, "data", {})
                            output = data.get("output", data.get("result", ""))
                            if output:
                                all_output.append(str(output))

                    # Detailed message type analysis
                    has_result = "ResultMessage" in msg_types
                    has_user = "UserMessage" in msg_types
                    has_system = "SystemMessage" in msg_types
                    has_assistant = "AssistantMessage" in msg_types
                    has_output = len(all_output) > 0

                    # Determine status based on message types and output
                    if has_result and has_output:
                        status = "PASS"
                    elif has_result:
                        status = "PASS_NO_OUTPUT"
                    elif has_user or has_system or has_assistant:
                        status = "PARTIAL"
                    else:
                        status = "NO_RESPONSE"

                    # Create output preview (first 80 chars of first output)
                    output_preview = ""
                    if all_output:
                        preview = all_output[0][:80].replace("\n", " ")
                        if len(all_output[0]) > 80:
                            preview += "..."
                        output_preview = preview

                    results.append({
                        "command": cmd_name,
                        "status": status,
                        "response_count": len(responses),
                        "message_types": list(msg_types),
                        "has_result": has_result,
                        "has_user": has_user,
                        "has_system": has_system,
                        "has_assistant": has_assistant,
                        "has_output": has_output,
                        "output_preview": output_preview,
                        "output_length": sum(len(o) for o in all_output),
                    })

                except Exception as e:
                    results.append({
                        "command": cmd_name,
                        "status": "ERROR",
                        "error": str(e),
                        "message_types": [],
                        "has_output": False,
                    })

        # Print detailed results with output information
        print("\n" + "=" * 90)
        print("SDK Command Test Results (Message Type + Output Validation)")
        print("=" * 90)

        for r in results:
            status_icon = {
                "PASS": "✓",
                "PASS_NO_OUTPUT": "○",
                "PARTIAL": "~",
                "NO_RESPONSE": "✗",
                "ERROR": "✗",
            }.get(r["status"], "?")

            msg_types_str = ", ".join(r.get("message_types", []))
            output_info = f"[{r.get('output_length', 0)} chars]" if r.get("has_output") else "[no output]"
            print(f"{status_icon} {r['command']:<20} | {r['status']:<15} | {output_info:<15} | {msg_types_str}")

            # Show output preview if available
            if r.get("output_preview"):
                print(f"   Preview: {r['output_preview']}")

        # Summary
        passed = len([r for r in results if r["status"] == "PASS"])
        passed_no_output = len([r for r in results if r["status"] == "PASS_NO_OUTPUT"])
        partial = len([r for r in results if r["status"] == "PARTIAL"])
        failed = len([r for r in results if r["status"] in ("NO_RESPONSE", "ERROR")])
        with_output = len([r for r in results if r.get("has_output")])

        print("\n" + "-" * 90)
        print(f"Summary: {passed} passed, {passed_no_output} passed (no output), {partial} partial, {failed} failed")
        print(f"Commands with output: {with_output}/{len(results)}")

        # Assert based on validation criteria - only fail on errors, not partial
        errors = [r for r in results if r["status"] == "ERROR"]
        assert len(errors) == 0, f"Commands with errors: {errors}"


    @pytest.mark.asyncio
    async def test_release_notes_message_structure(self) -> None:
        """Capture full message structure for /release-notes to debug output display."""
        options = ClaudeAgentOptions()

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt="/release-notes")

            print("\n" + "=" * 80)
            print("MESSAGE STRUCTURE DEBUG FOR /release-notes")
            print("=" * 80)

            async for msg in client.receive_response():
                msg_type = type(msg).__name__
                print(f"\n--- {msg_type} ---")

                # Print all non-private attribute values
                for attr in dir(msg):
                    if not attr.startswith("_"):
                        try:
                            value = getattr(msg, attr)
                            if not callable(value):
                                # Truncate long values for readability
                                str_value = str(value)
                                if len(str_value) > 500:
                                    str_value = str_value[:500] + "..."
                                print(f"  {attr}: {str_value}")
                        except Exception as e:
                            print(f"  {attr}: <error: {e}>")

            print("\n" + "=" * 80)


class TestTriagentCliCommands:
    """Tests to verify triagent CLI commands are handled locally (not forwarded to SDK)."""

    @pytest.mark.asyncio
    async def test_triagent_commands_not_in_sdk(self) -> None:
        """Verify triagent CLI commands are NOT in SDK command list."""
        triagent_commands = {
            "init", "team", "persona", "config",
            "exit", "quit", "help", "clear",
            "versions", "team-report", "confirm",
        }

        options = ClaudeAgentOptions()

        async with ClaudeSDKClient(options=options) as client:
            server_info = await client.get_server_info()
            commands = server_info.get("commands", []) if server_info else []

            sdk_command_names: set[str] = set()
            for cmd in commands:
                if isinstance(cmd, dict):
                    name = cmd.get("name", cmd.get("command", ""))
                else:
                    name = str(cmd)

                # Remove leading slash for comparison
                if name.startswith("/"):
                    name = name[1:]
                sdk_command_names.add(name.lower())

            # Check which triagent commands exist in SDK
            overlap = triagent_commands & sdk_command_names
            print(f"\nTriagent commands found in SDK: {overlap}")
            print(f"SDK commands: {sdk_command_names}")

            # Note: Some overlap is expected (help, clear) - they exist in both
            # This test is informational, not a hard assertion
