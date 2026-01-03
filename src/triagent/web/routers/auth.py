"""Azure authentication router for Triagent Web API."""

import json

from fastapi import APIRouter, Header, HTTPException

from triagent.web.models import AzureAuthResponse, AzureAuthStatusResponse
from triagent.web.services.session_proxy import SessionProxy

router = APIRouter(tags=["auth"])


@router.post("/auth/azure", response_model=AzureAuthResponse)
async def start_azure_auth(
    x_session_id: str = Header(..., alias="X-Session-ID"),
) -> AzureAuthResponse:
    """Start Azure CLI device code authentication.

    Args:
        x_session_id: Session ID from header.

    Returns:
        AzureAuthResponse with device code and verification URL.

    Raises:
        HTTPException: If device code flow fails to start.
    """
    proxy = SessionProxy()

    code = '''
import subprocess
import json
import re

result = subprocess.run(
    ["az", "login", "--use-device-code"],
    capture_output=True,
    text=True,
    timeout=30,
)

# Parse device code from stderr
match = re.search(r"code ([A-Z0-9-]+)", result.stderr)
if match:
    print(json.dumps({
        "device_code": match.group(1),
        "verification_url": "https://microsoft.com/devicelogin",
        "message": "Open the URL and enter the code to authenticate",
    }))
else:
    print(json.dumps({"error": "Failed to get device code"}))
'''
    try:
        result = await proxy.execute_code(x_session_id, code)
        stdout = result.get("properties", {}).get("stdout", "")

        if "error" in stdout:
            raise HTTPException(status_code=500, detail="Failed to start Azure auth")

        data = json.loads(stdout)
        return AzureAuthResponse(**data)

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse Azure auth response: {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start Azure auth: {e}",
        ) from e


@router.get("/auth/azure/status", response_model=AzureAuthStatusResponse)
async def check_azure_auth(
    x_session_id: str = Header(..., alias="X-Session-ID"),
) -> AzureAuthStatusResponse:
    """Check if Azure CLI authentication completed.

    Args:
        x_session_id: Session ID from header.

    Returns:
        AzureAuthStatusResponse with authentication status.
    """
    proxy = SessionProxy()

    code = '''
import subprocess
import json

result = subprocess.run(
    ["az", "account", "show", "--output", "json"],
    capture_output=True,
    text=True,
)

if result.returncode == 0:
    data = json.loads(result.stdout)
    print(json.dumps({
        "authenticated": True,
        "user": data.get("user", {}).get("name", ""),
        "subscription": data.get("name", ""),
        "tenant": data.get("tenantId", ""),
    }))
else:
    print(json.dumps({"authenticated": False, "message": "Not authenticated"}))
'''
    try:
        result = await proxy.execute_code(x_session_id, code)
        stdout = result.get("properties", {}).get("stdout", "")
        data = json.loads(stdout)
        return AzureAuthStatusResponse(**data)

    except json.JSONDecodeError:
        return AzureAuthStatusResponse(
            authenticated=False,
            message="Failed to check authentication status",
        )
    except Exception:
        return AzureAuthStatusResponse(
            authenticated=False,
            message="Failed to check authentication status",
        )
