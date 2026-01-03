"""Tests for authentication utilities."""

from triagent.web.auth import generate_session_id


def test_generate_session_id():
    """Test that session ID is generated correctly."""
    session_id = generate_session_id("user@example.com")
    assert session_id.startswith("triagent-")
    assert len(session_id) == 25  # triagent- (9) + 16 chars


def test_generate_session_id_deterministic():
    """Test that same email produces same session ID regardless of case."""
    id1 = generate_session_id("USER@example.com")
    id2 = generate_session_id("user@EXAMPLE.COM")
    assert id1 == id2  # Case-insensitive


def test_generate_session_id_different_emails():
    """Test that different emails produce different session IDs."""
    id1 = generate_session_id("user1@example.com")
    id2 = generate_session_id("user2@example.com")
    assert id1 != id2


def test_generate_session_id_with_special_chars():
    """Test session ID generation with special characters in email."""
    session_id = generate_session_id("user+tag@example.com")
    assert session_id.startswith("triagent-")
    assert len(session_id) == 25
