"""Session management router for Triagent Web API."""

from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException

from triagent.web.auth import generate_session_id, verify_api_key
from triagent.web.models import SessionCreateRequest, SessionResponse
from triagent.web.services.session_proxy import SessionProxy
from triagent.web.services.session_store import SessionStore

router = APIRouter(tags=["session"])


@router.post("/session", response_model=SessionResponse, status_code=201)
async def create_session(
    request: SessionCreateRequest,
    _: str = Depends(verify_api_key),
) -> SessionResponse:
    """Create a new triagent session.

    Args:
        request: Session creation request with email, team, and credentials.

    Returns:
        SessionResponse with session details.

    Raises:
        HTTPException: If session already exists (409) or initialization fails.
    """
    store = SessionStore()

    # Check if session already exists
    existing = await store.get_session(request.email)
    if existing:
        raise HTTPException(status_code=409, detail="Session already exists")

    # Generate session ID
    session_id = generate_session_id(request.email)

    # Initialize container via session pool
    proxy = SessionProxy()
    init_code = f'''
import json
from triagent.config import ConfigManager
manager = ConfigManager()
manager.ensure_dirs()
# Write credentials
creds = {{
    "api_provider": "{request.api_provider}",
    "anthropic_foundry_api_key": "{request.api_token}",
    "anthropic_foundry_base_url": "{request.api_base_url or ''}",
}}
manager.save_credentials(manager._credentials.__class__(**creds))
# Write config
config = {{"team": "{request.team}"}}
manager.save_config(manager._config.__class__(**config))
print("initialized")
'''
    try:
        await proxy.execute_code(session_id, init_code)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize session container: {e}",
        ) from e

    # Store session metadata
    session_data = await store.create_session(
        email=request.email,
        session_id=session_id,
        team=request.team,
        api_provider=request.api_provider,
    )

    return SessionResponse(
        session_id=session_data["session_id"],
        email=session_data["email"],
        team=session_data["team"],
        api_provider=session_data["api_provider"],
        created_at=datetime.fromisoformat(session_data["created_at"]),
        expires_at=datetime.fromisoformat(session_data["expires_at"]),
    )


@router.get("/session", response_model=SessionResponse)
async def get_session(
    x_session_id: str = Header(..., alias="X-Session-ID"),
) -> SessionResponse:
    """Get current session status.

    Args:
        x_session_id: Session ID from X-Session-ID header.

    Returns:
        Session metadata.

    Raises:
        HTTPException: If session not found (404).
    """
    store = SessionStore()
    session_data = await store.get_session_by_id(x_session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        session_id=session_data["session_id"],
        email=session_data["email"],
        team=session_data["team"],
        api_provider=session_data["api_provider"],
        created_at=datetime.fromisoformat(session_data["created_at"]),
        expires_at=datetime.fromisoformat(session_data["expires_at"]),
    )


@router.delete("/session", status_code=204)
async def delete_session(
    email: str,
    _: str = Depends(verify_api_key),
) -> None:
    """Delete a session.

    Args:
        email: Email of the session to delete.

    Raises:
        HTTPException: If session not found (404).
    """
    store = SessionStore()

    existing = await store.get_session(email)
    if not existing:
        raise HTTPException(status_code=404, detail="Session not found")

    await store.delete_session(email)
