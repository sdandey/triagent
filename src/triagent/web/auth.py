"""Authentication utilities for Triagent Web API."""

import hashlib

from fastapi import Header, HTTPException


def generate_session_id(email: str) -> str:
    """Generate deterministic session ID from email.

    Args:
        email: User's email address.

    Returns:
        Session ID in format 'triagent-{hash}'.
    """
    user_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:16]
    return f"triagent-{user_hash}"


async def verify_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> str:
    """Dependency to validate Triagent API key.

    Args:
        x_api_key: API key from X-API-Key header.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If API key is invalid.
    """
    from triagent.web.config import WebConfig

    config = WebConfig()
    if x_api_key != config.triagent_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
