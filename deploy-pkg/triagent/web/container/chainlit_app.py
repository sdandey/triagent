"""Chainlit chat interface for Triagent sessions."""

from typing import Any

import chainlit as cl
from claude_agent_sdk import ClaudeSDKClient
from rich.console import Console

from triagent.config import ConfigManager, TriagentConfig, TriagentCredentials
from triagent.sdk_client import create_sdk_client


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> cl.User | None:
    """Authenticate user with username/password.

    For development, accepts any username with password 'triagent'.
    In production, integrate with your identity provider.
    """
    # Development: accept any username with password "triagent"
    if password == "triagent":
        return cl.User(
            identifier=username,
            metadata={"role": "user", "provider": "credentials"},
        )
    return None


@cl.set_chat_profiles
async def set_chat_profiles(current_user: cl.User | None) -> list[cl.ChatProfile]:
    """Define available team profiles for session selection."""
    return [
        cl.ChatProfile(
            name="Omnia Data",
            markdown_description="Default team for Audit Cortex 2 project",
            default=True,
        ),
        cl.ChatProfile(
            name="Omnia",
            markdown_description="Omnia team",
        ),
        cl.ChatProfile(
            name="Levvia",
            markdown_description="Levvia team",
        ),
    ]


@cl.on_chat_start
async def on_chat_start() -> None:
    """Initialize session with SDK client, with setup wizard if needed."""
    config_manager = ConfigManager()

    # Get selected chat profile (team) from sidebar
    chat_profile = cl.user_session.get("chat_profile")
    if chat_profile:
        # Use profile as team selection (convert "Omnia Data" -> "omnia-data")
        team = chat_profile.lower().replace(" ", "-")
        cl.user_session.set("team", team)

    # Check if config exists - if not, run setup wizard
    if not config_manager.config_exists():
        await run_setup_wizard(config_manager)
        return

    # Config exists - initialize SDK client
    await initialize_sdk_client(config_manager)


async def run_setup_wizard(config_manager: ConfigManager) -> None:
    """Run interactive setup wizard to collect credentials."""
    # Welcome message
    await cl.Message(
        content="Welcome to **Triagent**! Let's set up your session."
    ).send()

    # Step 1: API Provider selection
    provider_res = await cl.AskActionMessage(
        content="**Step 1/4**: Select your API Provider:",
        actions=[
            cl.Action(
                name="azure_foundry",
                payload={"provider": "azure_foundry"},
                label="Azure AI Foundry",
            ),
            cl.Action(
                name="anthropic",
                payload={"provider": "anthropic"},
                label="Anthropic (Direct)",
            ),
        ],
    ).send()

    if not provider_res:
        await cl.Message(content="Setup cancelled.").send()
        return

    # Get provider from the action name
    api_provider: str = provider_res.get("name", "")
    if not api_provider:
        await cl.Message(content="Invalid selection. Setup cancelled.").send()
        return

    # Step 2: API Token
    token_res = await cl.AskUserMessage(
        content="**Step 2/4**: Enter your API token:",
        timeout=300,
    ).send()

    if not token_res:
        await cl.Message(content="Setup cancelled.").send()
        return

    api_token: str = str(token_res.get("output", "")).strip()
    if not api_token:
        await cl.Message(content="API token is required. Setup cancelled.").send()
        return

    # Step 3: Base URL (Azure Foundry only)
    api_base_url: str | None = None
    if api_provider == "azure_foundry":
        url_res = await cl.AskUserMessage(
            content=(
                "**Step 3/4**: Enter your Azure Foundry base URL:\n"
                "(e.g., `https://your-resource.openai.azure.com/`)"
            ),
            timeout=300,
        ).send()

        if not url_res:
            await cl.Message(content="Setup cancelled.").send()
            return

        api_base_url = str(url_res.get("output", "")).strip()
        if not api_base_url:
            await cl.Message(
                content="Base URL is required for Azure Foundry. Setup cancelled."
            ).send()
            return

    # Step 4: Team selection (skip if chat profile already selected)
    team: str | None = cl.user_session.get("team")

    if not team:
        step_num = "4/4" if api_provider == "azure_foundry" else "3/3"
        team_res = await cl.AskActionMessage(
            content=f"**Step {step_num}**: Select your team:",
            actions=[
                cl.Action(
                    name="omnia-data",
                    payload={"team": "omnia-data"},
                    label="Omnia Data (Default)",
                ),
                cl.Action(
                    name="omnia",
                    payload={"team": "omnia"},
                    label="Omnia",
                ),
                cl.Action(
                    name="levvia",
                    payload={"team": "levvia"},
                    label="Levvia",
                ),
            ],
        ).send()

        if not team_res:
            await cl.Message(content="Setup cancelled.").send()
            return

        team = team_res.get("name", "")
        if not team:
            await cl.Message(content="Invalid selection. Setup cancelled.").send()
            return

    # Save configuration
    await cl.Message(content="Initializing session...").send()

    try:
        await save_session_config(
            config_manager, api_provider, api_token, api_base_url, team
        )
        await initialize_sdk_client(config_manager)
    except Exception as e:
        await cl.Message(content=f"Failed to initialize: {e}").send()


async def save_session_config(
    config_manager: ConfigManager,
    api_provider: str,
    api_token: str,
    api_base_url: str | None,
    team: str,
) -> None:
    """Save credentials and config to ConfigManager."""
    config_manager.ensure_dirs()

    # Save credentials
    credentials = TriagentCredentials(
        api_provider=api_provider,
        anthropic_foundry_api_key=api_token,
        anthropic_foundry_base_url=api_base_url or "",
    )
    config_manager.save_credentials(credentials)

    # Save config
    config = TriagentConfig(team=team)
    config_manager.save_config(config)


async def initialize_sdk_client(config_manager: ConfigManager) -> None:
    """Initialize SDK client and store in session."""
    console = Console(force_terminal=False, no_color=True)
    client_factory = create_sdk_client(config_manager, console)
    options = client_factory._build_options()

    client = ClaudeSDKClient(options=options)
    await client.__aenter__()
    cl.user_session.set("sdk_client", client)

    await cl.Message(
        content="Connected to Claude! How can I help you with Azure DevOps today?"
    ).send()


@cl.on_chat_end
async def on_chat_end() -> None:
    """Cleanup SDK client on session end."""
    client = cl.user_session.get("sdk_client")
    if client:
        await client.__aexit__(None, None, None)


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """Handle incoming message with tool cards.

    Args:
        message: Incoming chat message.
    """
    client = cl.user_session.get("sdk_client")

    if not client:
        await cl.Message(
            content="Session not ready. Please refresh and try again."
        ).send()
        return

    # Send query to Claude
    await client.query(prompt=message.content)

    # Stream response with tool cards
    response_msg = cl.Message(content="")
    await response_msg.send()

    async for msg in client.receive_response():
        await process_sdk_message(msg, response_msg)


async def process_sdk_message(msg: Any, response_msg: cl.Message) -> None:
    """Process SDK message, create tool cards for tool_use blocks.

    Args:
        msg: SDK message object.
        response_msg: Chainlit message to update.
    """
    msg_type = type(msg).__name__

    if msg_type == "AssistantMessage":
        for block in msg.content:
            block_type = type(block).__name__

            if block_type == "TextBlock":
                response_msg.content += block.text
                await response_msg.update()

            elif block_type == "ToolUseBlock":
                # Create tool card
                async with cl.Step(name=block.name, type="tool") as step:
                    step.input = str(block.input)
                    # Tool execution happens via SDK
                    # Result will come in ToolResultMessage

    elif msg_type == "ToolResultMessage":
        # Update the last tool step with result
        # Chainlit handles this automatically via step context
        pass
