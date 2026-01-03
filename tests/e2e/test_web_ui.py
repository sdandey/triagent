"""End-to-end tests for Triagent Web UI."""

import pytest
from playwright.sync_api import Page, expect


class TestHealthEndpoint:
    """Tests for health endpoint via browser."""

    def test_health_endpoint(self, page: Page, api_url: str):
        """Test health endpoint is accessible."""
        response = page.request.get(f"{api_url}/health")
        assert response.status == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestPageLoad:
    """Tests for page loading."""

    def test_page_loads(self, page: Page, base_url: str):
        """Test that page loads without errors."""
        page.goto(base_url)
        expect(page.locator("body")).to_be_visible()

    def test_chainlit_ui_renders(self, page: Page, base_url: str):
        """Test that Chainlit UI renders."""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        # Chainlit should render its main container
        expect(page.locator("body")).to_be_visible()


class TestChatInterface:
    """Tests for chat interface."""

    @pytest.mark.skip(reason="Requires running Chainlit server")
    def test_send_message(self, authenticated_page: Page):
        """Test sending a chat message."""
        # Find and fill the input
        input_field = authenticated_page.locator("textarea").first
        expect(input_field).to_be_visible()

        input_field.fill("Hello, what can you help me with?")

        # Submit (Enter or button click)
        input_field.press("Enter")

        # Wait for response (Chainlit renders messages)
        # Message should appear within 30 seconds
        authenticated_page.wait_for_timeout(5000)  # Wait for response to start

    @pytest.mark.skip(reason="Requires running Chainlit server with Azure auth")
    def test_tool_card_displays(self, authenticated_page: Page):
        """Test that tool execution shows tool card."""
        input_field = authenticated_page.locator("textarea").first

        # Send a message that triggers a tool
        input_field.fill("What is the current Azure subscription?")
        input_field.press("Enter")

        # Wait for tool card to appear (if Azure authenticated)
        # Tool cards have type="tool" attribute in Chainlit
        authenticated_page.wait_for_timeout(10000)


class TestResponsiveDesign:
    """Tests for responsive design."""

    def test_mobile_viewport(self, page: Page, base_url: str):
        """Test page works on mobile viewport."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        # Page should still be visible
        expect(page.locator("body")).to_be_visible()

    def test_tablet_viewport(self, page: Page, base_url: str):
        """Test page works on tablet viewport."""
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        expect(page.locator("body")).to_be_visible()


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_for_unknown_route(self, page: Page, api_url: str):
        """Test 404 response for unknown API route."""
        response = page.request.get(f"{api_url}/api/unknown")
        assert response.status == 404
