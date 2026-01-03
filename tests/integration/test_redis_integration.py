"""Integration tests for Redis session store."""

import pytest

from triagent.web.services.session_store import SessionStore


@pytest.mark.asyncio
async def test_redis_session_create(redis_container):
    """Test creating a session in Redis."""
    store = SessionStore()

    session = await store.create_session(
        email="test@example.com",
        session_id="triagent-test123",
        team="omnia-data",
        api_provider="azure_foundry",
    )

    assert session["session_id"] == "triagent-test123"
    assert session["email"] == "test@example.com"
    assert session["team"] == "omnia-data"
    assert session["api_provider"] == "azure_foundry"

    await store.close()


@pytest.mark.asyncio
async def test_redis_session_get(redis_container):
    """Test retrieving a session from Redis."""
    store = SessionStore()

    # Create first
    await store.create_session(
        email="get-test@example.com",
        session_id="triagent-get123",
        team="omnia-data",
        api_provider="anthropic",
    )

    # Retrieve
    session = await store.get_session("get-test@example.com")
    assert session is not None
    assert session["api_provider"] == "anthropic"
    assert session["session_id"] == "triagent-get123"

    await store.close()


@pytest.mark.asyncio
async def test_redis_session_not_found(redis_container):
    """Test retrieving non-existent session returns None."""
    store = SessionStore()

    session = await store.get_session("nonexistent@example.com")
    assert session is None

    await store.close()


@pytest.mark.asyncio
async def test_redis_session_ttl(redis_container):
    """Test that sessions have correct TTL."""
    store = SessionStore()

    await store.create_session(
        email="ttl-test@example.com",
        session_id="triagent-ttl123",
        team="omnia-data",
        api_provider="azure_foundry",
    )

    # Check TTL is set (should be around 7200 seconds)
    ttl = await store.redis.ttl("session:user:ttl-test@example.com")
    assert 7100 < ttl <= 7200

    await store.close()


@pytest.mark.asyncio
async def test_redis_session_delete(redis_container):
    """Test deleting a session from Redis."""
    store = SessionStore()

    # Create
    await store.create_session(
        email="delete-test@example.com",
        session_id="triagent-del123",
        team="omnia-data",
        api_provider="anthropic",
    )

    # Verify exists
    session = await store.get_session("delete-test@example.com")
    assert session is not None

    # Delete
    await store.delete_session("delete-test@example.com")

    # Verify deleted
    session = await store.get_session("delete-test@example.com")
    assert session is None

    await store.close()


@pytest.mark.asyncio
async def test_redis_session_update_last_active(redis_container):
    """Test updating last_active timestamp."""
    store = SessionStore()

    # Create
    await store.create_session(
        email="active-test@example.com",
        session_id="triagent-active123",
        team="omnia-data",
        api_provider="azure_foundry",
    )

    # Get original last_active
    session1 = await store.get_session("active-test@example.com")
    original_last_active = session1["last_active"]

    # Wait a tiny bit and update
    import asyncio
    await asyncio.sleep(0.1)
    await store.update_last_active("active-test@example.com")

    # Check updated
    session2 = await store.get_session("active-test@example.com")
    assert session2["last_active"] != original_last_active

    await store.close()


@pytest.mark.asyncio
async def test_redis_session_update_azure_auth(redis_container):
    """Test updating Azure authentication status."""
    store = SessionStore()

    # Create
    await store.create_session(
        email="auth-test@example.com",
        session_id="triagent-auth123",
        team="omnia-data",
        api_provider="azure_foundry",
    )

    # Verify initially not authenticated
    session = await store.get_session("auth-test@example.com")
    assert session["azure_authenticated"] is False

    # Update to authenticated
    await store.update_azure_auth("auth-test@example.com", True)

    # Verify updated
    session = await store.get_session("auth-test@example.com")
    assert session["azure_authenticated"] is True

    await store.close()


@pytest.mark.asyncio
async def test_redis_session_get_by_id(redis_container):
    """Test retrieving a session by session ID (reverse lookup)."""
    store = SessionStore()

    # Create session
    await store.create_session(
        email="id-lookup-test@example.com",
        session_id="triagent-idlookup123",
        team="omnia-data",
        api_provider="anthropic",
    )

    # Retrieve by session ID
    session = await store.get_session_by_id("triagent-idlookup123")
    assert session is not None
    assert session["email"] == "id-lookup-test@example.com"
    assert session["session_id"] == "triagent-idlookup123"
    assert session["api_provider"] == "anthropic"

    await store.close()


@pytest.mark.asyncio
async def test_redis_session_get_by_id_not_found(redis_container):
    """Test retrieving non-existent session by ID returns None."""
    store = SessionStore()

    session = await store.get_session_by_id("nonexistent-session-id")
    assert session is None

    await store.close()


@pytest.mark.asyncio
async def test_redis_session_reverse_index_cleanup(redis_container):
    """Test that reverse index is cleaned up when session is deleted."""
    store = SessionStore()

    # Create session
    await store.create_session(
        email="cleanup-test@example.com",
        session_id="triagent-cleanup123",
        team="omnia-data",
        api_provider="azure_foundry",
    )

    # Verify both keys exist
    session_by_email = await store.get_session("cleanup-test@example.com")
    session_by_id = await store.get_session_by_id("triagent-cleanup123")
    assert session_by_email is not None
    assert session_by_id is not None

    # Delete session
    await store.delete_session("cleanup-test@example.com")

    # Verify both lookups return None
    session_by_email = await store.get_session("cleanup-test@example.com")
    session_by_id = await store.get_session_by_id("triagent-cleanup123")
    assert session_by_email is None
    assert session_by_id is None

    await store.close()


@pytest.mark.asyncio
async def test_redis_session_reverse_index_ttl(redis_container):
    """Test that reverse index has same TTL as session."""
    store = SessionStore()

    await store.create_session(
        email="ttl-idx-test@example.com",
        session_id="triagent-ttlidx123",
        team="omnia-data",
        api_provider="azure_foundry",
    )

    # Check both keys have correct TTL
    user_ttl = await store.redis.ttl("session:user:ttl-idx-test@example.com")
    id_ttl = await store.redis.ttl("session:id:triagent-ttlidx123")

    assert 7100 < user_ttl <= 7200
    assert 7100 < id_ttl <= 7200

    await store.close()
