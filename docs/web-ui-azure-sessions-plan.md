# Triagent Web UI with Azure Container Apps Dynamic Sessions

**Document Version:** 1.2
**Prepared by:** sdandey
**Last Updated:** 2025-12-30 11:30:00 CST

## Table of Contents

1. [Overview](#overview)
2. [Ready-to-Use Chat Interface Options](#ready-to-use-chat-interface-options)
3. [User Experience Flow](#user-experience-flow)
4. [Azure CLI Authentication](#azure-cli-authentication-device-code-flow)
5. [Architecture](#architecture)
6. [Implementation Phases](#implementation-phases)
7. [File Structure](#file-structure)
8. [Dependencies](#dependencies)
9. [User Steps to Use](#user-steps-to-use-final-experience)
10. [Session Identification and Storage Design](#session-identification-and-storage-design)
11. [MVP Authentication](#mvp-authentication-api-key--self-reported-username)
12. [Security Considerations](#security-considerations)
13. [Sources](#sources)

---

## Overview

Build a web-based chat interface for Triagent using Azure Container Apps dynamic sessions. Each user gets an isolated container sandbox with all dependencies pre-installed, persisting for up to 2 hours.

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| UI Framework | Chainlit | Python-native, built-in tool UI, zero frontend code |
| UI Hosting | Azure App Service | Better production scaling, separate from sessions |
| Authentication | API Key/Token | Simple auth for internal/dev use |
| Session Model | Per-user sessions | One container per user, shared across conversations |
| Feature Scope | Full feature parity | All CLI features (/init, /team, /config, etc.) |

---

## Ready-to-Use Chat Interface Options

### Recommended: **Chainlit**

[Chainlit](https://chainlit.io/) is an open-source Python framework for building LLM chat interfaces with minimal code.

**Why Chainlit:**
- **Python-native** - Works directly with existing triagent Python code
- **Built-in tool execution UI** - Shows tool calls, inputs, and results (perfect for Azure CLI operations)
- **Streaming support** - Real-time response streaming via WebSocket
- **Multi-step actions** - Native support for wizards (like /init)
- **Apache 2.0 license** - Free for commercial use
- **Zero frontend code** - Focus on Python logic only

**Installation:**
```bash
pip install chainlit
```

**Basic integration:**
```python
import chainlit as cl

@cl.on_chat_start
async def start():
    # Initialize triagent session
    pass

@cl.on_message
async def main(message: cl.Message):
    # Route to triagent agent
    pass
```

### Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Gradio** | Quick setup, `gr.ChatInterface` | Less suited for tool-heavy workflows |
| **Open WebUI** | Full-featured, OpenAI-compatible | Opinionated, harder to customize for custom tools |
| **Streamlit** | Popular, easy | Not ideal for real-time streaming |
| **Custom React** | Full control | Significant development effort |

---

## User Experience Flow

### The Challenge

Each Azure Container Apps session is an **ephemeral container** with:
- No persistent storage across sessions
- No pre-configured Azure CLI authentication
- No saved API credentials

Users must configure and authenticate **for each new session**.

### Proposed User Journey

```
+------------------------------------------------------------------+
|  FIRST TIME / NEW SESSION FLOW                                   |
+------------------------------------------------------------------+
|                                                                  |
|  1. User opens web UI                                            |
|           |                                                      |
|           v                                                      |
|  2. Backend checks for existing session                          |
|     +-- No session -> Show "Session Setup" screen                |
|           |                                                      |
|           v                                                      |
|  3. SESSION SETUP WIZARD (Web Form)                              |
|     +-------------------------------------------------------+    |
|     |  Step 1: API Provider                                 |    |
|     |  o Databricks (recommended)                           |    |
|     |  o Azure AI Foundry                                   |    |
|     |  o Direct Anthropic API                               |    |
|     |                                                       |    |
|     |  [API Base URL: _____________]                        |    |
|     |  [API Token: _______________]                         |    |
|     |  [Model: ___________________]                         |    |
|     |                                                       |    |
|     |  Step 2: Team Selection                               |    |
|     |  o Levvia                                             |    |
|     |  o Omnia                                              |    |
|     |  o Omnia Data (recommended)                           |    |
|     |                                                       |    |
|     |  [Create Session]                                     |    |
|     +-------------------------------------------------------+    |
|           |                                                      |
|           v                                                      |
|  4. Backend creates Azure Container Apps session                 |
|     +-- Injects credentials via /init endpoint                   |
|           |                                                      |
|           v                                                      |
|  5. AZURE CLI AUTHENTICATION (In-Chat)                           |
|     +-------------------------------------------------------+    |
|     |  [LOCK] Azure Authentication Required                 |    |
|     |                                                       |    |
|     |  To use Azure DevOps tools, authenticate with:        |    |
|     |                                                       |    |
|     |  1. Open: https://microsoft.com/devicelogin           |    |
|     |  2. Enter code: ABCD-EFGH                             |    |
|     |                                                       |    |
|     |  [Open Link]  [I've Authenticated]                    |    |
|     +-------------------------------------------------------+    |
|           |                                                      |
|           v                                                      |
|  6. User authenticates via device code flow                      |
|           |                                                      |
|           v                                                      |
|  7. Chat interface ready - user can interact                     |
|                                                                  |
+------------------------------------------------------------------+
```

### Returning User (Session Exists)

```
+------------------------------------------------------------------+
|  RETURNING USER FLOW                                             |
+------------------------------------------------------------------+
|                                                                  |
|  1. User opens web UI                                            |
|           |                                                      |
|           v                                                      |
|  2. Backend checks for existing session (via user ID)            |
|     +-- Session found (not expired) -> Reconnect                 |
|           |                                                      |
|           v                                                      |
|  3. Chat interface ready - previous context preserved            |
|                                                                  |
|  Note: Session idle timeout = 30 min (configurable)              |
|        After timeout, user goes through "New Session" flow       |
|                                                                  |
+------------------------------------------------------------------+
```

---

## Azure CLI Authentication: Device Code Flow

Since containers can't open a browser, use Azure CLI's **device code flow**:

```bash
az login --use-device-code
```

This outputs:
```
To sign in, use a web browser to open the page https://microsoft.com/devicelogin
and enter the code ABCD-EFGH to authenticate.
```

### Implementation in Container

**In `src/triagent/web/container/triagent_api.py`:**

```python
@router.post("/auth/azure")
async def start_azure_auth():
    """Initiate Azure CLI device code authentication."""
    import subprocess

    # Start az login with device code
    result = subprocess.run(
        ["az", "login", "--use-device-code"],
        capture_output=True,
        text=True,
        timeout=10  # Just to capture the device code
    )

    # Parse device code from output
    # "To sign in, use a web browser to open https://microsoft.com/devicelogin
    #  and enter the code ABCD-EFGH"
    import re
    match = re.search(r'code\s+([A-Z0-9-]+)', result.stderr)

    if match:
        return {
            "device_code": match.group(1),
            "url": "https://microsoft.com/devicelogin",
            "message": "Open the URL and enter the code to authenticate"
        }

    raise HTTPException(500, "Failed to get device code")

@router.post("/auth/azure/complete")
async def complete_azure_auth():
    """Wait for Azure authentication to complete."""
    import subprocess

    # Check if logged in
    result = subprocess.run(
        ["az", "account", "show"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        import json
        account = json.loads(result.stdout)
        return {
            "authenticated": True,
            "user": account.get("user", {}).get("name"),
            "subscription": account.get("name")
        }

    return {"authenticated": False}
```

---

## Comparison: CLI vs Web Experience

| Step | Current CLI | Proposed Web UI |
|------|-------------|-----------------|
| **Start** | Run `triagent` | Open URL |
| **API Config** | Interactive prompts in `/init` | Web form (Step 1) |
| **Team Selection** | Number selection in `/init` | Dropdown (Step 2) |
| **Azure Auth** | Browser popup via `az login` | Device code link in chat |
| **Chat** | Terminal input/output | Web chat interface |
| **Tool Status** | Spinner + text | Visual tool execution cards |
| **Confirmation** | y/n prompt | Modal dialog |
| **Session Persist** | Local files | Container (30 min idle timeout) |

---

## Architecture

```
+-----------------------------------------------------------------------------+
|                              USER'S BROWSER                                 |
|  +-----------------------------------------------------------------------+  |
|  |  Chainlit Web UI                                                      |  |
|  |  - Chat messages                                                      |  |
|  |  - Tool execution cards                                               |  |
|  |  - Confirmation dialogs                                               |  |
|  |  - Session setup wizard                                               |  |
|  +-----------------------------------------------------------------------+  |
+-------------------------------------+---------------------------------------+
                                      | HTTP/WebSocket
                                      v
+-----------------------------------------------------------------------------+
|                     AZURE APP SERVICE (FastAPI Backend)                     |
|  +-----------------------------------------------------------------------+  |
|  |  - Session Manager (maps user -> container session)                   |  |
|  |  - Credential injection (pass API keys to container)                  |  |
|  |  - Authentication (API key middleware)                                |  |
|  |  - Proxy requests to container sessions                               |  |
|  +-----------------------------------------------------------------------+  |
|                                      |                                      |
|                           +----------+----------+                           |
|                           v                     v                           |
|                  +-----------------+   +-----------------+                  |
|                  |  Redis Cache    |   |  (Optional)     |                  |
|                  |  Session Map    |   |  Cosmos DB      |                  |
|                  |  user -> session|   |  Chat History   |                  |
|                  +-----------------+   +-----------------+                  |
+-------------------------------------+---------------------------------------+
                                      | HTTP (via Azure AD token)
                                      v
+-----------------------------------------------------------------------------+
|              AZURE CONTAINER APPS SESSION POOL                              |
|  +-----------------------------------------------------------------------+  |
|  |  Session 1 (User A)                                                   |  |
|  |  +-------------------------------------------------------------------+|  |
|  |  |  triagent container                                               ||  |
|  |  |  - Python 3.11 + triagent                                         ||  |
|  |  |  - Azure CLI + extensions                                         ||  |
|  |  |  - Node.js + MCP servers                                          ||  |
|  |  |  - FastAPI HTTP server (port 8080)                                ||  |
|  |  |                                                                   ||  |
|  |  |  Endpoints:                                                       ||  |
|  |  |  - POST /chat          (process message)                          ||  |
|  |  |  - POST /chat/stream   (SSE streaming)                            ||  |
|  |  |  - POST /init          (apply config)                             ||  |
|  |  |  - POST /auth/azure    (device code flow)                         ||  |
|  |  |  - GET  /config        (get current config)                       ||  |
|  |  +-------------------------------------------------------------------+|  |
|  +-----------------------------------------------------------------------+  |
|  +-----------------------------------------------------------------------+  |
|  |  Session 2 (User B)  ...                                              |  |
|  +-----------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------+
```

---

## Implementation Phases

### Phase 1: Chainlit Integration (Container-side)

Create Chainlit app that runs inside the container.

**Files to create:**
- `src/triagent/web/chainlit_app.py` - Main Chainlit application
- `src/triagent/web/chainlit_handlers.py` - Message and tool handlers

**Key Chainlit features to use:**
- `@cl.on_chat_start` - Session initialization
- `@cl.on_message` - Message handling
- `@cl.step` - Tool execution visualization
- `cl.AskUserMessage` - Confirmation dialogs
- `cl.AskActionMessage` - Azure auth device code prompt

### Phase 2: Session Backend (App Service)

Build FastAPI backend that manages sessions and proxies to containers.

**Files to create:**
- `src/triagent/web/app.py` - FastAPI application
- `src/triagent/web/services/session_manager.py` - Azure Sessions integration
- `src/triagent/web/services/session_store.py` - Redis session mapping

### Phase 3: Container Image

Build custom container for Azure Container Apps sessions.

**Files to modify:**
- `Dockerfile.session` - New Dockerfile for session containers

**Container requirements:**
- Python 3.11 + triagent + Chainlit
- Azure CLI + extensions
- Node.js + MCP servers
- HTTP server on port 8080

### Phase 4: Azure Deployment

Deploy infrastructure:
1. Container Registry (ACR) - Store session image
2. Container Apps Environment (workload profiles enabled)
3. Session Pool (custom container type)
4. App Service - FastAPI backend
5. Redis Cache - Session mapping

---

## File Structure

### New Files

```
src/triagent/web/
├── __init__.py
├── chainlit_app.py              # Chainlit chat application
├── chainlit_handlers.py         # Message/tool handlers
├── app.py                       # FastAPI backend
├── config.py                    # Web configuration
├── services/
│   ├── __init__.py
│   ├── session_manager.py       # Azure Sessions client
│   └── session_store.py         # Redis session mapping
└── container/
    ├── http_server.py           # Container HTTP server
    └── Dockerfile.session       # Session container image
```

### Files to Modify

| File | Changes |
|------|---------|
| `pyproject.toml` | Add `[project.optional-dependencies] web = [...]` |

---

## Dependencies

### pyproject.toml additions

```toml
[project.optional-dependencies]
web = [
    "chainlit>=2.0.0",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "redis>=5.0.0",
    "azure-identity>=1.18.0",
]
```

---

## User Steps to Use (Final Experience)

### First Time Setup

1. **Open web UI** in browser
2. **Configure API Provider** via web form:
   - Select Databricks/Azure Foundry/Anthropic
   - Enter API URL and token
   - Select team
3. **Click "Create Session"** - Backend creates container
4. **Authenticate Azure CLI** via device code:
   - Chat displays: "Open https://microsoft.com/devicelogin and enter code: ABCD-EFGH"
   - User opens link in new tab, enters code, logs in
   - Click "I've Authenticated" in chat
5. **Start chatting** - Full triagent functionality available

### Returning User

1. **Open web UI** - Session automatically reconnects if still active
2. **Start chatting** - Previous context preserved
3. If session expired → Go through First Time Setup again

### Session Timeout Behavior

- **Idle timeout**: 30 minutes (configurable via `--cooldown-period`)
- **Max session duration**: 2 hours (Azure Container Apps limit)
- After timeout, user sees "Session expired" message and setup wizard

---

## Session Identification and Storage Design

### The Problem

When a user opens the web UI, the backend must:
1. Identify the user (authentication)
2. Determine if they have an existing session (lookup)
3. Create a new session or reconnect to existing (session management)
4. Store the mapping between user and session (persistence)

Azure Container Apps Sessions API requires a **session identifier** (4-128 chars) when calling endpoints. If a session with that ID doesn't exist, Azure automatically creates one.

### Session Identification Options

#### Option A: User ID-Based Sessions (Recommended)

**Concept**: One container session per authenticated user. The session identifier is derived from the user's identity.

**Session ID Format**: `triagent-{user_hash}` where `user_hash = sha256(user_email)[:16]`

**Example**: `triagent-a1b2c3d4e5f67890`

**Flow**:
```
User opens UI → Authenticate → Generate session_id from user identity
                                       ↓
                              Call Session Pool API with session_id
                                       ↓
                              Azure auto-creates if new, reuses if exists
```

**Redis Data Structure**:
```json
{
  "key": "session:user:{user_email}",
  "value": {
    "session_id": "triagent-a1b2c3d4e5f67890",
    "created_at": "2025-12-29T12:00:00Z",
    "last_active": "2025-12-29T14:30:00Z",
    "team": "omnia-data",
    "api_provider": "databricks",
    "azure_authenticated": true
  },
  "ttl": 7200  // 2 hours (matches Azure max session lifetime)
}
```

**Pros**:
- Deterministic - same user always gets same session
- Simple lookup - no need to search, just compute the ID
- Session survives browser refresh/close (until timeout)
- Natural multi-device support (same user on phone/laptop gets same session)

**Cons**:
- User can only have one active session at a time
- No conversation isolation (all chats in same container)

---

#### Option B: Conversation-Based Sessions

**Concept**: Each new chat conversation creates a new container session.

**Session ID Format**: `triagent-{uuid4}`

**Example**: `triagent-550e8400-e29b-41d4-a716-446655440000`

**Flow**:
```
User opens UI → Authenticate → Generate new UUID for session_id
                                       ↓
                              Store session_id in browser (localStorage/cookie)
                                       ↓
                              Call Session Pool API with session_id
```

**Redis Data Structure**:
```json
{
  "key": "session:conversation:{session_id}",
  "value": {
    "session_id": "triagent-550e8400-...",
    "user_email": "user@example.com",
    "created_at": "2025-12-29T12:00:00Z",
    "last_active": "2025-12-29T14:30:00Z",
    "team": "omnia-data",
    "conversation_title": "Debug PR #1234"
  },
  "ttl": 7200
}

// Index for user lookup
{
  "key": "user:sessions:{user_email}",
  "value": ["triagent-550e8400-...", "triagent-662f9511-..."],
  "ttl": 86400  // 24 hours
}
```

**Pros**:
- Multiple parallel sessions per user
- Conversation isolation (different contexts don't mix)
- Better for power users with multiple tasks

**Cons**:
- More complex - need to track multiple sessions
- Session lost if browser localStorage cleared
- Higher container resource usage

---

#### Option C: Hybrid Approach

**Concept**: Default to user-based sessions, but allow explicit "New Session" for parallel work.

**Session ID Format**:
- Primary: `triagent-{user_hash}` (default session)
- Additional: `triagent-{user_hash}-{slot_number}` (slots 1-5)

**Example**:
- Default: `triagent-a1b2c3d4e5f67890`
- Slot 2: `triagent-a1b2c3d4e5f67890-2`

**Redis Data Structure**:
```json
{
  "key": "session:user:{user_email}:active_slot",
  "value": "0",  // 0 = default, 1-5 = additional slots
  "ttl": 7200
}

{
  "key": "session:user:{user_email}:slots",
  "value": {
    "0": {"session_id": "triagent-a1b2c3d4e5f67890", "title": "Default", "last_active": "..."},
    "2": {"session_id": "triagent-a1b2c3d4e5f67890-2", "title": "PR Review", "last_active": "..."}
  },
  "ttl": 7200
}
```

**Pros**:
- Best of both worlds
- Simple default experience
- Power users can create additional sessions

**Cons**:
- Most complex to implement
- UI needs session switcher

---

### Recommended Approach: Option A (User ID-Based)

For the initial implementation, **Option A** is recommended because:

1. **Simplicity**: Deterministic session IDs eliminate race conditions
2. **UX**: Users expect to return to their session after browser refresh
3. **Cost**: One container per user is more resource-efficient
4. **Security**: Session ID derived from authenticated identity, not guessable

---

## MVP Authentication: API Key + Self-Reported Username

Due to Azure AD App Registration restrictions (requires IAM team involvement), the MVP uses a simpler authentication mechanism:

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     MVP AUTHENTICATION FLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. USER OPENS WEB UI                                                   │
│         │                                                               │
│         v                                                               │
│  2. SESSION SETUP FORM                                                  │
│     +-------------------------------------------------------+          │
│     |  Email:     [user@example.com_____]                   |          │
│     |  API Key:   [**************************]              |          │
│     |  Team:      [Omnia Data ▼]                            |          │
│     |  Provider:  [Databricks ▼]                            |          │
│     |                                                       |          │
│     |  [Create Session]                                     |          │
│     +-------------------------------------------------------+          │
│         │                                                               │
│         v                                                               │
│  3. BACKEND VALIDATES API KEY                                           │
│     - Check: request.api_key == TRIAGENT_API_KEY                        │
│     - If invalid: 401 Unauthorized                                      │
│         │                                                               │
│         v                                                               │
│  4. GENERATE SESSION ID FROM EMAIL                                      │
│     - session_id = triagent-{sha256(email)[:16]}                        │
│         │                                                               │
│         v                                                               │
│  5. STORE IN REDIS + CREATE CONTAINER SESSION                           │
│         │                                                               │
│         v                                                               │
│  6. CHAT READY                                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Configuration (Already Deployed)

| Setting | Value |
|---------|-------|
| **AUTH_MODE** | `api_key` |
| **TRIAGENT_API_KEY** | Stored in App Service config (secure) |

### FastAPI Implementation

```python
# src/triagent/web/auth.py
import os
import hashlib
from fastapi import HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr

class SessionSetupRequest(BaseModel):
    """Request model for session setup."""
    email: EmailStr           # User's email (self-reported)
    api_key: str              # Shared API key for authorization
    team: str                 # Team selection: levvia, omnia, omnia-data
    api_provider: str         # API provider: databricks, azure_foundry, anthropic
    api_base_url: str = ""    # API base URL (for databricks/foundry)
    api_token: str = ""       # API token for Claude provider

def verify_api_key(api_key: str) -> bool:
    """Verify the provided API key matches the configured key."""
    expected_key = os.environ.get("TRIAGENT_API_KEY", "")
    if not expected_key:
        raise HTTPException(500, "Server not configured with API key")
    return api_key == expected_key

def generate_session_id(email: str) -> str:
    """Generate deterministic session ID from user email."""
    user_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:16]
    return f"triagent-{user_hash}"

# API endpoint
@app.post("/api/session/setup")
async def setup_session(request: SessionSetupRequest):
    """Setup a new session for the user."""
    # Validate API key
    if not verify_api_key(request.api_key):
        raise HTTPException(401, "Invalid API key")

    # Generate session ID from email
    session_id = generate_session_id(request.email)

    # Store session metadata in Redis
    session_data = await session_store.create_session(
        user_email=request.email,
        session_id=session_id,
        team=request.team,
        api_provider=request.api_provider
    )

    return {
        "session_id": session_id,
        "message": "Session created successfully",
        "email": request.email
    }
```

### Security Notes

1. **API Key Distribution**: Share the API key only with authorized users (team members)
2. **Email Not Verified**: User email is self-reported (trust-based for MVP)
3. **HTTPS Only**: All traffic encrypted in transit
4. **Upgrade Path**: When Azure AD is available, replace with MSAL/Easy Auth

### Future: Azure AD Integration

When IAM team provides an App Registration:

1. Enable App Service Easy Auth with the provided Client ID
2. Change `AUTH_MODE` to `azure_ad`
3. Get verified user email from `X-MS-CLIENT-PRINCIPAL-NAME` header
4. Remove API key validation (Azure handles auth)

### Implementation Details

#### 1. Session ID Generation

```python
# src/triagent/web/services/session_manager.py
import hashlib

def generate_session_id(user_email: str) -> str:
    """Generate deterministic session ID from user email."""
    user_hash = hashlib.sha256(user_email.lower().encode()).hexdigest()[:16]
    return f"triagent-{user_hash}"
```

#### 2. Redis Session Store

```python
# src/triagent/web/services/session_store.py
import redis
import json
from datetime import datetime, timedelta

class SessionStore:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.session_ttl = 7200  # 2 hours

    def get_session(self, user_email: str) -> dict | None:
        """Get session metadata for user."""
        key = f"session:user:{user_email}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def create_session(self, user_email: str, session_id: str, team: str, api_provider: str) -> dict:
        """Create or update session metadata."""
        key = f"session:user:{user_email}"
        session_data = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat(),
            "team": team,
            "api_provider": api_provider,
            "azure_authenticated": False
        }
        self.redis.setex(key, self.session_ttl, json.dumps(session_data))
        return session_data

    def update_last_active(self, user_email: str):
        """Update last active timestamp and refresh TTL."""
        key = f"session:user:{user_email}"
        data = self.redis.get(key)
        if data:
            session_data = json.loads(data)
            session_data["last_active"] = datetime.utcnow().isoformat()
            self.redis.setex(key, self.session_ttl, json.dumps(session_data))
```

#### 3. Session Pool API Authentication

The FastAPI backend authenticates to Azure Container Apps Session Pool using Microsoft Entra tokens:

```python
# src/triagent/web/services/session_manager.py
from azure.identity import DefaultAzureCredential

class SessionManager:
    def __init__(self, pool_endpoint: str):
        self.pool_endpoint = pool_endpoint
        self.credential = DefaultAzureCredential()

    async def get_access_token(self) -> str:
        """Get token for Session Pool API."""
        # Scope for Container Apps Sessions
        scope = "https://dynamicsessions.io/.default"
        token = self.credential.get_token(scope)
        return token.token

    async def execute_in_session(self, session_id: str, code: str) -> dict:
        """Execute code in a session container."""
        token = await self.get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.pool_endpoint}/code/execute",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Identifier": session_id,
                    "Content-Type": "application/json"
                },
                json={"properties": {"codeInputType": "inline", "executionType": "synchronous", "code": code}}
            )
            return response.json()
```

#### 4. RBAC Requirements

The App Service managed identity needs the **Azure ContainerApps Session Executor** role on the Session Pool:

```bicep
// modules/sessionPoolRbac.bicep
resource sessionExecutorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(sessionPool.id, appServicePrincipalId, 'session-executor')
  scope: sessionPool
  properties: {
    principalId: appServicePrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '0fb8eba5-a2bb-4abe-b1c1-49dfad359bb0')
    principalType: 'ServicePrincipal'
  }
}
```

### Session Lifecycle Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SESSION LIFECYCLE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. USER OPENS WEB UI                                                   │
│         │                                                               │
│         v                                                               │
│  2. AUTHENTICATE USER (API key / OAuth)                                 │
│         │                                                               │
│         v                                                               │
│  3. GENERATE SESSION ID: triagent-{sha256(email)[:16]}                  │
│         │                                                               │
│         v                                                               │
│  4. CHECK REDIS: Does session metadata exist?                           │
│         │                                                               │
│    ┌────┴────┐                                                          │
│    │         │                                                          │
│   YES       NO                                                          │
│    │         │                                                          │
│    v         v                                                          │
│  5a. Return  5b. Show Session Setup Wizard                              │
│  existing       │                                                       │
│  session        v                                                       │
│    │       6. User configures: API provider, team                       │
│    │            │                                                       │
│    │            v                                                       │
│    │       7. Call Session Pool API (auto-creates container)            │
│    │            │                                                       │
│    │            v                                                       │
│    │       8. POST /init to container with credentials                  │
│    │            │                                                       │
│    │            v                                                       │
│    │       9. Store session metadata in Redis (TTL: 2hr)                │
│    │            │                                                       │
│    └────────────┘                                                       │
│         │                                                               │
│         v                                                               │
│  10. CHAT READY - proxy messages to container                           │
│         │                                                               │
│         v                                                               │
│  11. ON EACH MESSAGE: Update last_active in Redis, refresh TTL          │
│         │                                                               │
│         v                                                               │
│  12. TIMEOUT (idle 30min or max 2hr):                                   │
│      - Azure destroys container                                         │
│      - Redis TTL expires                                                │
│      - Next visit → back to step 4 (no metadata found → setup wizard)   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Security Considerations

1. **Credentials in transit**: HTTPS only, encrypted
2. **Credentials in container**: Stored in `~/.triagent/credentials.json` (container-local)
3. **Azure auth**: Device code flow - user authenticates via browser, no password in container
4. **Session isolation**: Hyper-V sandbox per container
5. **API keys**: Validated by backend middleware before proxying to container
6. **Session ID security**: Derived from authenticated user identity via SHA-256 hash - not enumerable or guessable

---

## Sources

- [Chainlit Documentation](https://docs.chainlit.io/)
- [Chainlit with Custom Tools](https://deepwiki.com/Chainlit/cookbook/7-function-calling-and-tool-integration)
- [Azure Container Apps Dynamic Sessions](https://learn.microsoft.com/en-us/azure/container-apps/sessions)
- [Custom Container Sessions](https://learn.microsoft.com/en-us/azure/container-apps/sessions-custom-container)
- [Azure CLI Device Code Login](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli-interactively)
- [Open WebUI](https://github.com/open-webui/open-webui)
- [Gradio ChatInterface](https://www.gradio.app/docs/gradio/chatinterface)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-29 | sdandey | Initial plan document |
| 1.1 | 2025-12-30 | sdandey | Added Session Identification and Storage Design section with 3 options (User ID-based, Conversation-based, Hybrid), implementation details, Redis data structures, RBAC requirements, and session lifecycle flow |
| 1.2 | 2025-12-30 | sdandey | Added MVP Authentication section (API Key + Self-Reported Username) due to Azure AD restrictions. Updated Bicep templates with AUTH_MODE and TRIAGENT_API_KEY settings |
