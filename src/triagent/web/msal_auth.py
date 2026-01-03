"""MSAL authentication utilities for Triagent Web API."""

import logging

import httpx

logger = logging.getLogger(__name__)


async def validate_group_membership(access_token: str, group_id: str) -> bool:
    """Check if user is member of specified Azure AD group via Microsoft Graph API.

    Args:
        access_token: User's access token from OAuth flow.
        group_id: Azure AD group object ID to check membership.

    Returns:
        True if user is member of the group, False otherwise.
    """
    if not group_id:
        return True  # No group restriction configured

    url = "https://graph.microsoft.com/v1.0/me/memberOf"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)

            if response.status_code != 200:
                logger.warning(
                    f"Failed to check group membership: {response.status_code}"
                )
                return False

            data = response.json()
            groups = data.get("value", [])

            for group in groups:
                if group.get("id") == group_id:
                    logger.info(f"User is member of group {group_id}")
                    return True

            logger.warning(f"User is not a member of group {group_id}")
            return False

        except httpx.HTTPError as e:
            logger.error(f"HTTP error checking group membership: {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking group membership: {e}")
            return False
