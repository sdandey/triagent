"""Chainlit chat interface for Triagent sessions with Dynamic Sessions."""

import json
import logging
from typing import Any

import chainlit as cl

from triagent.web.config import WebConfig
from triagent.web.container.session_manager import (
    ChainlitSessionManager,
    SessionCredentials,
)
from triagent.web.msal_auth import validate_group_membership

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@cl.oauth_callback
async def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict[str, Any],
    default_user: cl.User,
) -> cl.User | None:
    """Handle Azure AD OAuth callback.

    Args:
        provider_id: The OAuth provider ID (e.g., "azure-ad").
        token: Access token from Azure AD.
        raw_user_data: User info from Microsoft Graph API.
        default_user: Default user object created by Chainlit.

    Returns:
        cl.User if authenticated successfully, None to reject.
    """
    if provider_id != "azure-ad":
        logger.warning(f"Unexpected OAuth provider: {provider_id}")
        return None

    # Extract user info from Azure AD claims
    email = raw_user_data.get("mail") or raw_user_data.get("userPrincipalName", "")
    display_name = raw_user_data.get("displayName", email)

    logger.info(f"OAuth callback for user: {email} (provider: {provider_id})")

    # Optional: Validate AD group membership
    config = WebConfig()
    if config.allowed_ad_group_id:
        is_member = await validate_group_membership(token, config.allowed_ad_group_id)
        if not is_member:
            logger.warning(f"User {email} not in allowed AD group")
            return None

    return cl.User(
        identifier=email,
        metadata={
            "provider": "azure-ad",
            "display_name": display_name,
            "role": "user",
        },
    )


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
    """Initialize Dynamic Session for user."""
    user = cl.user_session.get("user")
    if not user:
        await cl.Message(content="Authentication required.").send()
        return

    # Generate session ID from username
    session_id = ChainlitSessionManager.generate_session_id(user.identifier)
    cl.user_session.set("session_id", session_id)
    logger.info(f"Generated session ID: {session_id} for user: {user.identifier}")

    # Get team from chat profile
    chat_profile = cl.user_session.get("chat_profile")
    team = chat_profile.lower().replace(" ", "-") if chat_profile else "omnia-data"
    cl.user_session.set("team", team)

    # Initialize session manager
    manager = ChainlitSessionManager()
    cl.user_session.set("session_manager", manager)

    # Show connecting message immediately (fixes blank screen issue)
    await cl.Message(content="Connecting to Dynamic Session...").send()

    # Run setup wizard to collect credentials and initialize Dynamic Session
    await run_setup_wizard(manager, session_id, team)


async def run_setup_wizard(
    manager: ChainlitSessionManager, session_id: str, team: str
) -> None:
    """Run setup wizard and initialize Dynamic Session.

    Args:
        manager: The ChainlitSessionManager instance.
        session_id: The Dynamic Session identifier.
        team: The selected team name.
    """
    # Welcome message
    await cl.Message(
        content="Welcome to **Triagent**! Let's set up your session."
    ).send()

    # Step 1: API Provider selection
    provider_res = await cl.AskActionMessage(
        content="**Step 1/3**: Select your API Provider:",
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

    api_provider: str = provider_res.get("name", "")
    if not api_provider:
        await cl.Message(content="Invalid selection. Setup cancelled.").send()
        return

    # Step 2: API Token
    token_res = await cl.AskUserMessage(
        content="**Step 2/3**: Enter your API token:",
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
                "**Step 3/3**: Enter your Azure Foundry base URL:\n"
                "(e.g., `https://your-resource.services.ai.azure.com/`)"
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

    # Initialize Dynamic Session
    await cl.Message(content="Initializing Dynamic Session...").send()

    try:
        credentials = SessionCredentials(
            api_provider=api_provider,
            api_token=api_token,
            api_base_url=api_base_url,
            team=team,
        )
        result = await manager.initialize_session(session_id, credentials)
        logger.info(f"Session initialization result: {result}")

        await cl.Message(
            content="Connected to Claude! How can I help you with Azure DevOps today?"
        ).send()

    except Exception as e:
        logger.exception(f"Failed to initialize Dynamic Session: {e}")
        await cl.Message(
            content=f"**Failed to connect**: {e}\n\nPlease check your credentials and try again."
        ).send()


@cl.on_chat_end
async def on_chat_end() -> None:
    """Cleanup session manager on session end."""
    manager = cl.user_session.get("session_manager")
    if manager:
        await manager.close()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """Route message to Dynamic Session and stream response.

    Args:
        message: Incoming chat message.
    """
    manager: ChainlitSessionManager | None = cl.user_session.get("session_manager")
    session_id: str | None = cl.user_session.get("session_id")

    if not manager or not session_id:
        await cl.Message(
            content="Session not ready. Please refresh and try again."
        ).send()
        return

    # Create response message
    response_msg = cl.Message(content="")
    await response_msg.send()

    # Stream response from Dynamic Session
    try:
        async for chunk in manager.send_message(session_id, message.content):
            await process_response_chunk(chunk, response_msg)
    except Exception as e:
        logger.exception(f"Error streaming response: {e}")
        response_msg.content = f"**Error**: {e}"
        await response_msg.update()


async def process_response_chunk(chunk: str, response_msg: cl.Message) -> None:
    """Process a response chunk from the Dynamic Session.

    Args:
        chunk: JSON string or raw text chunk from SDK.
        response_msg: Chainlit message to update.
    """
    try:
        data: dict[str, Any] = json.loads(chunk)
        msg_type = data.get("type", "")

        if msg_type == "text":
            response_msg.content += data.get("content", "")
            await response_msg.update()

        elif msg_type == "tool":
            async with cl.Step(name=data.get("name", "tool"), type="tool") as step:
                step.input = data.get("input", "")

        elif msg_type == "error":
            error_content = data.get("content", "Unknown error")
            response_msg.content += f"\n**Error**: {error_content}"
            await response_msg.update()

    except json.JSONDecodeError:
        # Raw text chunk (non-JSON output from container)
        if chunk.strip():
            response_msg.content += chunk
            await response_msg.update()
