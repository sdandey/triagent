"""Redis session store for Triagent Web API."""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import redis.asyncio as redis

from triagent.web.config import WebConfig


class SessionStore:
    """Redis-based session metadata storage."""

    def __init__(self) -> None:
        """Initialize session store with Redis connection."""
        config = WebConfig()
        self.redis = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            password=config.redis_password or None,
            ssl=config.redis_ssl,
            decode_responses=True,
        )
        self.ttl = config.session_ttl

    async def get_session(self, email: str) -> dict[str, Any] | None:
        """Get session metadata by email.

        Args:
            email: User's email address.

        Returns:
            Session metadata dict or None if not found.
        """
        key = f"session:user:{email.lower()}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def get_session_by_id(self, session_id: str) -> dict[str, Any] | None:
        """Get session metadata by session ID.

        Args:
            session_id: The session ID.

        Returns:
            Session metadata dict or None if not found.
        """
        # Look up email from reverse index
        id_key = f"session:id:{session_id}"
        email = await self.redis.get(id_key)
        if not email:
            return None
        return await self.get_session(email)

    async def create_session(
        self,
        email: str,
        session_id: str,
        team: str,
        api_provider: str,
    ) -> dict[str, Any]:
        """Create new session metadata.

        Args:
            email: User's email address.
            session_id: Generated session ID.
            team: Team name.
            api_provider: API provider (azure_foundry or anthropic).

        Returns:
            Created session metadata.
        """
        key = f"session:user:{email.lower()}"
        now = datetime.now(UTC)
        session_data = {
            "session_id": session_id,
            "email": email,
            "team": team,
            "api_provider": api_provider,
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(seconds=self.ttl)).isoformat(),
            "last_active": now.isoformat(),
            "azure_authenticated": False,
            "container_status": "ready",
        }
        await self.redis.setex(key, self.ttl, json.dumps(session_data))
        # Store reverse index: session_id -> email
        id_key = f"session:id:{session_id}"
        await self.redis.setex(id_key, self.ttl, email.lower())
        return session_data

    async def update_last_active(self, email: str) -> None:
        """Update last_active timestamp.

        Args:
            email: User's email address.
        """
        key = f"session:user:{email.lower()}"
        data = await self.redis.get(key)
        if data:
            session = json.loads(data)
            session["last_active"] = datetime.now(UTC).isoformat()
            ttl = await self.redis.ttl(key)
            if ttl > 0:
                await self.redis.setex(key, ttl, json.dumps(session))

    async def update_azure_auth(self, email: str, authenticated: bool) -> None:
        """Update Azure authentication status.

        Args:
            email: User's email address.
            authenticated: Whether Azure CLI is authenticated.
        """
        key = f"session:user:{email.lower()}"
        data = await self.redis.get(key)
        if data:
            session = json.loads(data)
            session["azure_authenticated"] = authenticated
            ttl = await self.redis.ttl(key)
            if ttl > 0:
                await self.redis.setex(key, ttl, json.dumps(session))

    async def delete_session(self, email: str) -> None:
        """Delete session metadata.

        Args:
            email: User's email address.
        """
        key = f"session:user:{email.lower()}"
        # Get session to find session_id for reverse index cleanup
        data = await self.redis.get(key)
        if data:
            session = json.loads(data)
            session_id = session.get("session_id")
            if session_id:
                id_key = f"session:id:{session_id}"
                await self.redis.delete(id_key)
        await self.redis.delete(key)

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis.close()
