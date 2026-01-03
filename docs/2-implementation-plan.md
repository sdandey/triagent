# Triagent Web UI - Implementation Plan

**Document Version:** 2.1
**Prepared by:** sdandey
**Last Updated:** 2025-12-30
**Status:** Ready for Implementation
**Infrastructure:** Already provisioned (Bicep deployed)

---

## Table of Contents

1. [Recent Codebase Changes](#recent-codebase-changes-pr-19)
2. [Existing Codebase Analysis](#existing-codebase-analysis)
3. [Implementation Phases](#implementation-phases)
4. [Phase 1: Project Setup](#phase-1-project-setup--dependencies)
5. [Phase 2: FastAPI Backend](#phase-2-fastapi-backend-app-service)
6. [Phase 3: Chainlit UI](#phase-3-chainlit-ui-container)
7. [Phase 4: Container Image](#phase-4-session-container-image)
8. [Phase 5: Testing](#phase-5-integration--testing)
9. [Phase 6: E2E Tests](#phase-6-playwright-e2e-tests)
10. [Phase 7: Integration Testing Strategy](#phase-7-integration-testing-strategy)
11. [Files Summary](#files-to-createmodify)
12. [Verification Commands](#verification-commands)

---

## Recent Codebase Changes (PR #19)

**Merged:** `feat: remove --legacy CLI flag and Databricks implementation`

Key changes affecting web implementation:
- **Removed Databricks provider** - only `azure_foundry` and `anthropic` supported
- **Default provider:** Changed from `databricks` to `azure_foundry`
- **TriagentCredentials:** Removed all Databricks-specific fields
- **Agent SDK only:** No more legacy DatabricksClient implementation

**Supported API Providers:**

| Provider | Description | Requires Base URL |
|----------|-------------|-------------------|
| `azure_foundry` | Azure AI Foundry endpoint (default) | Yes |
| `anthropic` | Direct Anthropic API | No |

---

## Existing Codebase Analysis

The triagent-web-ui repository already has:
- **Source:** `src/triagent/` with full CLI implementation
- **Agent SDK:** Uses `claude-agent-sdk` with `ClaudeSDKClient`
- **SDK Client:** `sdk_client.py` - builds `ClaudeAgentOptions`
- **Config:** `config.py` - `TriagentConfig`, `TriagentCredentials`, `ConfigManager`
- **Hooks:** `hooks.py` - security hooks for write confirmations
- **Dockerfile.web:** Uses ttyd for web terminal (existing approach)

**TriagentCredentials (from config.py:66-103):**
```python
@dataclass
class TriagentCredentials:
    # API Provider: "azure_foundry" | "anthropic"
    api_provider: str = "azure_foundry"

    # Azure Foundry credentials
    anthropic_foundry_api_key: str = ""
    anthropic_foundry_resource: str = ""
    anthropic_foundry_base_url: str = ""
    anthropic_foundry_model: str = "claude-opus-4-5"

    # ADO credentials
    ado_pat: str = ""
```

**Key Reusable Components:**
- `sdk_client.py:TriagentSDKClient._build_options()` - agent configuration
- `config.py:ConfigManager` - credential and config management
- `hooks.py:get_triagent_hooks()` - security hooks
- `prompts/system.py:get_system_prompt()` - team-specific prompts

---

## Implementation Phases

| Phase | Description | Tasks |
|-------|-------------|-------|
| 1 | Project Setup & Dependencies | 3 |
| 2 | FastAPI Backend (App Service) | 7 |
| 3 | Chainlit UI (Container) | 5 |
| 4 | Session Container Image | 3 |
| 5 | Integration & Testing | 4 |
| 6 | Playwright E2E Tests | 3 |
| 7 | Integration Testing Strategy | 8 |
| **Total** | | **33** |

---

## Phase 1: Project Setup & Dependencies

### 1.1 Update pyproject.toml with web dependencies

**File:** `pyproject.toml`

Add to existing optional-dependencies:
```toml
[project.optional-dependencies]
# ... existing dev dependencies ...
web = [
    "chainlit>=2.0.0",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "redis>=5.0.0",
    "azure-identity>=1.18.0",
    "sse-starlette>=2.0.0",
    "pydantic-settings>=2.0.0",
]

test-web = [
    "pytest-playwright>=0.5.0",
    "playwright>=1.40.0",
]
```

### 1.2 Create web package structure

**Create directories under existing `src/triagent/`:**
```
src/triagent/web/
├── __init__.py
├── app.py                    # FastAPI main application
├── config.py                 # Web-specific config (extends base config)
├── auth.py                   # API key validation, session ID generation
├── models.py                 # Pydantic request/response models
├── routers/
│   ├── __init__.py
│   ├── session.py            # POST/GET /api/session
│   ├── chat.py               # POST /api/chat/stream (SSE)
│   ├── auth.py               # POST /api/auth/azure
│   └── health.py             # GET /health
└── services/
    ├── __init__.py
    ├── session_store.py      # Redis session metadata
    └── session_proxy.py      # Proxy to Azure Container Apps Session Pool
```

### 1.3 Create Chainlit container structure

**Create under `src/triagent/web/`:**
```
src/triagent/web/container/
├── __init__.py
├── chainlit_app.py           # Chainlit chat interface
├── handlers.py               # Tool execution handlers
└── .chainlit/
    └── config.toml           # Chainlit configuration
```

---

## Phase 2: FastAPI Backend (App Service)

### 2.1 Create web configuration

**File:** `src/triagent/web/config.py`

Extends base config, adds web-specific settings:
```python
from pydantic_settings import BaseSettings
from triagent.config import ConfigManager  # Reuse existing

class WebConfig(BaseSettings):
    """Web-specific configuration (loaded from environment)."""
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6380
    redis_password: str = ""
    redis_ssl: bool = True

    # Azure Session Pool
    session_pool_endpoint: str = ""

    # Authentication
    triagent_api_key: str = ""  # Shared API key for backend auth

    # Session settings
    session_ttl: int = 7200  # 2 hours

    class Config:
        env_prefix = "TRIAGENT_"
```

### 2.2 Create Pydantic models

**File:** `src/triagent/web/models.py`

```python
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Literal

class SessionCreateRequest(BaseModel):
    """Request to create a new triagent session."""
    email: str
    api_key: str  # Triagent API key (shared secret)
    team: str = "omnia-data"
    # Only azure_foundry and anthropic supported (no databricks)
    api_provider: Literal["azure_foundry", "anthropic"] = "azure_foundry"
    # Azure Foundry specific
    api_base_url: str | None = None  # Required for azure_foundry
    api_token: str  # LLM provider token

    @field_validator("api_base_url")
    @classmethod
    def validate_base_url(cls, v, info):
        if info.data.get("api_provider") == "azure_foundry" and not v:
            raise ValueError("api_base_url required for azure_foundry provider")
        return v

class SessionResponse(BaseModel):
    session_id: str
    email: str
    team: str
    api_provider: str
    created_at: datetime
    expires_at: datetime

class ChatRequest(BaseModel):
    message: str

class AzureAuthResponse(BaseModel):
    device_code: str
    verification_url: str
    message: str

class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict | None = None
```

### 2.3 Create authentication middleware

**File:** `src/triagent/web/auth.py`

```python
import hashlib
from fastapi import Header, HTTPException, Depends

def generate_session_id(email: str) -> str:
    """Generate deterministic session ID from email."""
    user_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:16]
    return f"triagent-{user_hash}"

async def verify_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> str:
    """Dependency to validate Triagent API key."""
    from triagent.web.config import WebConfig
    config = WebConfig()
    if x_api_key != config.triagent_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
```

### 2.4 Create Redis session store

**File:** `src/triagent/web/services/session_store.py`

```python
import redis.asyncio as redis
import json
from datetime import datetime, timedelta
from triagent.web.config import WebConfig

class SessionStore:
    def __init__(self):
        config = WebConfig()
        self.redis = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            password=config.redis_password,
            ssl=config.redis_ssl,
            decode_responses=True,
        )
        self.ttl = config.session_ttl

    async def get_session(self, email: str) -> dict | None:
        """Get session metadata by email."""
        key = f"session:user:{email.lower()}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def create_session(
        self,
        email: str,
        session_id: str,
        team: str,
        api_provider: str,
    ) -> dict:
        """Create new session metadata."""
        key = f"session:user:{email.lower()}"
        now = datetime.utcnow()
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
        return session_data

    async def update_last_active(self, email: str) -> None:
        """Update last_active timestamp."""
        key = f"session:user:{email.lower()}"
        data = await self.redis.get(key)
        if data:
            session = json.loads(data)
            session["last_active"] = datetime.utcnow().isoformat()
            ttl = await self.redis.ttl(key)
            await self.redis.setex(key, ttl, json.dumps(session))

    async def update_azure_auth(self, email: str, authenticated: bool) -> None:
        """Update Azure authentication status."""
        key = f"session:user:{email.lower()}"
        data = await self.redis.get(key)
        if data:
            session = json.loads(data)
            session["azure_authenticated"] = authenticated
            ttl = await self.redis.ttl(key)
            await self.redis.setex(key, ttl, json.dumps(session))

    async def delete_session(self, email: str) -> None:
        """Delete session metadata."""
        key = f"session:user:{email.lower()}"
        await self.redis.delete(key)
```

### 2.5 Create session proxy

**File:** `src/triagent/web/services/session_proxy.py`

```python
import httpx
from azure.identity.aio import DefaultAzureCredential
from triagent.web.config import WebConfig

class SessionProxy:
    """Proxy requests to Azure Container Apps Session Pool."""

    def __init__(self):
        self.config = WebConfig()
        self._credential = None

    async def get_access_token(self) -> str:
        """Get token for dynamicsessions.io scope."""
        if self._credential is None:
            self._credential = DefaultAzureCredential()
        token = await self._credential.get_token("https://dynamicsessions.io/.default")
        return token.token

    async def execute_code(self, session_id: str, code: str) -> dict:
        """Execute code in session container."""
        token = await self.get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.session_pool_endpoint}/code/execute",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Identifier": session_id,
                    "Content-Type": "application/json",
                },
                json={
                    "properties": {
                        "codeInputType": "inline",
                        "executionType": "synchronous",
                        "code": code,
                    }
                },
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()

    async def stream_chat(self, session_id: str, message: str):
        """Stream chat response from container."""
        token = await self.get_access_token()

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.config.session_pool_endpoint}/code/execute",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Identifier": session_id,
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
                json={
                    "properties": {
                        "codeInputType": "inline",
                        "executionType": "synchronous",
                        "code": f'await handle_chat_message("{message}")',
                    }
                },
                timeout=120.0,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        yield line
```

### 2.6 Create routers

**File:** `src/triagent/web/routers/health.py`

```python
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }
```

**File:** `src/triagent/web/routers/session.py`

```python
from fastapi import APIRouter, HTTPException, Header, Depends
from triagent.web.models import SessionCreateRequest, SessionResponse
from triagent.web.auth import generate_session_id, verify_api_key
from triagent.web.services.session_store import SessionStore
from triagent.web.services.session_proxy import SessionProxy
from datetime import datetime

router = APIRouter(tags=["session"])

@router.post("/session", response_model=SessionResponse, status_code=201)
async def create_session(
    request: SessionCreateRequest,
    _: str = Depends(verify_api_key),
):
    """Create a new triagent session."""
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
creds = {{
    "api_provider": "{request.api_provider}",
    "anthropic_foundry_api_key": "{request.api_token}",
    "anthropic_foundry_base_url": "{request.api_base_url or ''}",
}}
manager.save_credentials(manager._credentials.__class__(**creds))
config = {{"team": "{request.team}"}}
manager.save_config(manager._config.__class__(**config))
print("initialized")
'''
    await proxy.execute_code(session_id, init_code)

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
```

**File:** `src/triagent/web/routers/chat.py`

```python
from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse
from triagent.web.models import ChatRequest
from triagent.web.services.session_proxy import SessionProxy

router = APIRouter(tags=["chat"])

@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    x_session_id: str = Header(..., alias="X-Session-ID"),
):
    """Send message and receive streaming SSE response."""
    proxy = SessionProxy()

    async def generate():
        async for event in proxy.stream_chat(x_session_id, request.message):
            yield event + "\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
```

### 2.7 Create main FastAPI app

**File:** `src/triagent/web/app.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from triagent.web.routers import health, session, chat, auth

app = FastAPI(
    title="Triagent Web API",
    description="Web API for Triagent Azure DevOps automation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(session.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
```

---

## Phase 3: Chainlit UI (Container)

### 3.1 Create Chainlit configuration

**File:** `src/triagent/web/container/.chainlit/config.toml`

```toml
[project]
enable_telemetry = false

[features]
prompt_playground = false
unsafe_allow_javascript = false

[UI]
name = "Triagent"
show_readme_as_default = false
default_collapse_content = true
hide_cot = false
```

### 3.2 Create Chainlit app

**File:** `src/triagent/web/container/chainlit_app.py`

```python
import chainlit as cl
from claude_agent_sdk import ClaudeSDKClient
from triagent.config import ConfigManager
from triagent.sdk_client import create_sdk_client

@cl.on_chat_start
async def on_chat_start():
    """Initialize session with SDK client."""
    config_manager = ConfigManager()

    if not config_manager.config_exists():
        await cl.Message(
            content="Session not initialized. Please create a session via the API first."
        ).send()
        return

    client_factory = create_sdk_client(config_manager)
    options = client_factory._build_options()

    client = ClaudeSDKClient(options=options)
    await client.__aenter__()
    cl.user_session.set("sdk_client", client)

    await cl.Message(
        content="Connected to Claude. How can I help you with Azure DevOps today?"
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming message with tool cards."""
    client = cl.user_session.get("sdk_client")

    if not client:
        await cl.Message(content="Session not ready. Please refresh.").send()
        return

    await client.query(prompt=message.content)

    response_msg = cl.Message(content="")
    await response_msg.send()

    async for msg in client.receive_response():
        await process_sdk_message(msg, response_msg)

async def process_sdk_message(msg, response_msg: cl.Message):
    """Process SDK message, create tool cards for tool_use blocks."""
    msg_type = type(msg).__name__

    if msg_type == "AssistantMessage":
        for block in msg.content:
            block_type = type(block).__name__
            if block_type == "TextBlock":
                response_msg.content += block.text
                await response_msg.update()
            elif block_type == "ToolUseBlock":
                async with cl.Step(name=block.name, type="tool") as step:
                    step.input = str(block.input)
```

### 3.3 Create startup script

**File:** `src/triagent/web/container/start.sh`

```bash
#!/bin/bash
uvicorn triagent.web.container.api:container_app --host 0.0.0.0 --port 8081 &
chainlit run src/triagent/web/container/chainlit_app.py --host 0.0.0.0 --port 8080
```

---

## Phase 4: Session Container Image

### 4.1 Create Dockerfile.chainlit

**File:** `Dockerfile.chainlit`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git ca-certificates gnupg lsb-release sudo \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

ENV AZURE_EXTENSION_DIR=/opt/az/extensions
RUN mkdir -p /opt/az/extensions && \
    az extension add --name azure-devops --version 1.0.2 -y && \
    az extension add --name application-insights --version 2.0.0b1 -y --allow-preview true && \
    az extension add --name log-analytics --version 1.0.0b1 -y --allow-preview true

RUN pip install --upgrade pip uv

COPY pyproject.toml README.md ./
COPY src/ src/

RUN uv pip install --system -e ".[web]"

RUN useradd -m -u 1000 -s /bin/bash triagent && chown -R triagent:triagent /app

USER triagent
ENV NPM_CONFIG_PREFIX=/home/triagent/.npm-global
ENV PATH=$PATH:/home/triagent/.npm-global/bin
RUN mkdir -p /home/triagent/.triagent /home/triagent/.npm-global /home/triagent/.azure

ENV TERM=xterm-256color
ENV TRIAGENT_DOCKER=1
EXPOSE 8080 8081

COPY src/triagent/web/container/start.sh /start.sh
USER root
RUN chmod +x /start.sh
USER triagent

CMD ["/start.sh"]
```

### 4.2 Build and push container image

**Registry:** GitHub Container Registry (ghcr.io)

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u sdandey --password-stdin
docker build -f Dockerfile.chainlit -t ghcr.io/sdandey/triagent-chainlit:latest .
docker push ghcr.io/sdandey/triagent-chainlit:latest
```

---

## Phase 5: Integration & Testing

### 5.1 Create test fixtures

**File:** `tests/web/conftest.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from triagent.web.app import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def valid_api_key():
    return "test-api-key-12345"

@pytest.fixture
def mock_config(valid_api_key):
    with patch("triagent.web.config.WebConfig") as mock:
        config = MagicMock()
        config.triagent_api_key = valid_api_key
        config.redis_host = "localhost"
        config.session_ttl = 7200
        mock.return_value = config
        yield config
```

### 5.2 Create unit tests

**File:** `tests/web/test_auth.py`

```python
from triagent.web.auth import generate_session_id

def test_generate_session_id():
    session_id = generate_session_id("user@example.com")
    assert session_id.startswith("triagent-")
    assert len(session_id) == 25

def test_generate_session_id_deterministic():
    id1 = generate_session_id("USER@example.com")
    id2 = generate_session_id("user@EXAMPLE.COM")
    assert id1 == id2
```

**File:** `tests/web/test_models.py`

```python
import pytest
from pydantic import ValidationError
from triagent.web.models import SessionCreateRequest

def test_session_create_request_azure_requires_base_url():
    with pytest.raises(ValidationError):
        SessionCreateRequest(
            email="test@example.com",
            api_key="test-key",
            api_provider="azure_foundry",
            api_token="test-token",
        )

def test_session_create_request_invalid_provider():
    with pytest.raises(ValidationError):
        SessionCreateRequest(
            email="test@example.com",
            api_key="test-key",
            api_provider="databricks",  # Invalid
            api_token="test-token",
        )
```

---

## Phase 6: Playwright E2E Tests

### 6.1 Create E2E tests

**File:** `tests/e2e/test_web_ui.py`

```python
from playwright.sync_api import Page, expect

def test_health_endpoint(page: Page, base_url: str):
    response = page.request.get(f"{base_url}/health")
    assert response.status == 200

def test_page_loads(page: Page, base_url: str):
    page.goto(base_url)
    expect(page.locator("body")).to_be_visible()
```

### 6.2 Run E2E tests

```bash
playwright install chromium
pytest tests/e2e/ -v --browser chromium
```

---

## Phase 7: Integration Testing Strategy

This section covers how to perform integration testing during development, validating Redis integration, session API endpoints, and deploying components to Azure for validation.

### 7.1 Testing Layers Overview

| Layer | Tools | Purpose | Environment |
|-------|-------|---------|-------------|
| **Unit Tests** | pytest, mocks | Fast, isolated logic tests | Local |
| **Local Integration** | testcontainers, Docker | Redis, FastAPI with real containers | Local Docker |
| **Azure Sandbox** | Staging slot, sandbox RG | Full cloud integration | Azure (sandbox) |
| **E2E Tests** | Playwright | Browser-based UI testing | Azure or Local |

### 7.2 Local Integration Testing with Testcontainers

**Purpose:** Test Redis integration and FastAPI endpoints without deploying to Azure.

**Add dependencies to `pyproject.toml`:**
```toml
[project.optional-dependencies]
test-integration = [
    "testcontainers[redis]>=4.8.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
]
```

**File:** `tests/integration/conftest.py`

```python
import pytest
from testcontainers.redis import RedisContainer
from httpx import AsyncClient, ASGITransport
import os

@pytest.fixture(scope="session")
def redis_container():
    """Start Redis container for entire test session."""
    with RedisContainer("redis:7-alpine") as redis:
        os.environ["TRIAGENT_REDIS_HOST"] = redis.get_container_host_ip()
        os.environ["TRIAGENT_REDIS_PORT"] = str(redis.get_exposed_port(6379))
        os.environ["TRIAGENT_REDIS_PASSWORD"] = ""
        os.environ["TRIAGENT_REDIS_SSL"] = "false"
        yield redis

@pytest.fixture
async def async_client(redis_container):
    """Async HTTP client for FastAPI app."""
    from triagent.web.app import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture
def test_api_key():
    """Set test API key."""
    os.environ["TRIAGENT_TRIAGENT_API_KEY"] = "test-integration-key"
    return "test-integration-key"
```

**File:** `tests/integration/test_redis_integration.py`

```python
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
    ttl = await store.redis.ttl("session:user:ttl-test@example.com")
    assert 7100 < ttl <= 7200
```

**Run Local Integration Tests:**
```bash
uv pip install -e ".[test-integration]"
pytest tests/integration/ -v
```

### 7.3 Azure Sandbox Environment Testing

**Purpose:** Validate components against real Azure services (Redis Cache, Session Pool, App Service).

**Infrastructure Already Provisioned:**
- Resource Group: `triagent-sandbox-rg`
- Redis Cache: `triagent-sandbox-redis.redis.cache.windows.net:6380`
- Session Pool: `triagent-sandbox-session-pool`
- App Service: `triagent-sandbox-app.azurewebsites.net`

**File:** `scripts/deploy-sandbox.sh`

```bash
#!/bin/bash
set -e

RESOURCE_GROUP="triagent-sandbox-rg"
APP_NAME="triagent-sandbox-app"

echo "=== Deploying to Azure Sandbox ==="
cd /Users/sdandey/Documents/code/triagent-web-ui
uv pip install -e ".[web]"

rm -rf deploy-pkg && mkdir deploy-pkg
cp -r src/triagent deploy-pkg/
cp pyproject.toml README.md deploy-pkg/
cd deploy-pkg && zip -r ../app.zip . && cd ..

az webapp deploy --name $APP_NAME --resource-group $RESOURCE_GROUP --src-path app.zip --type zip

echo "Verifying deployment..."
curl -s "https://${APP_NAME}.azurewebsites.net/health" | jq .
```

**File:** `tests/azure/conftest.py`

```python
import os
import pytest
import httpx

SANDBOX_URL = os.environ.get("TRIAGENT_SANDBOX_URL", "https://triagent-sandbox-app.azurewebsites.net")
SANDBOX_API_KEY = os.environ.get("TRIAGENT_SANDBOX_API_KEY", "")

@pytest.fixture
def sandbox_api_key():
    if not SANDBOX_API_KEY:
        pytest.skip("TRIAGENT_SANDBOX_API_KEY not set")
    return SANDBOX_API_KEY

@pytest.fixture
async def sandbox_client(sandbox_api_key):
    async with httpx.AsyncClient(
        base_url=SANDBOX_URL,
        headers={"X-API-Key": sandbox_api_key},
        timeout=30.0,
    ) as client:
        yield client
```

**File:** `tests/azure/test_session_pool_api.py`

```python
import pytest
import subprocess
import httpx
import os

def get_azure_token():
    """Get Azure access token for dynamicsessions.io."""
    result = subprocess.run(
        ["az", "account", "get-access-token",
         "--resource", "https://dynamicsessions.io",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        pytest.skip("Azure CLI not authenticated")
    return result.stdout.strip()

@pytest.fixture
async def session_pool_client():
    endpoint = os.environ.get("TRIAGENT_SESSION_POOL_ENDPOINT", "")
    if not endpoint:
        pytest.skip("TRIAGENT_SESSION_POOL_ENDPOINT not set")
    token = get_azure_token()
    async with httpx.AsyncClient(
        base_url=endpoint,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=60.0,
    ) as client:
        yield client

@pytest.mark.asyncio
async def test_session_pool_execute_code(session_pool_client):
    """Test executing Python code in session pool."""
    test_session_id = f"test-{os.urandom(8).hex()}"
    response = await session_pool_client.post(
        "/code/execute",
        headers={"Identifier": test_session_id},
        json={
            "properties": {
                "codeInputType": "inline",
                "executionType": "synchronous",
                "code": "print('Hello from session pool!')",
            }
        },
    )
    assert response.status_code == 200
    assert "Hello from session pool!" in response.json().get("properties", {}).get("stdout", "")
```

**Run Azure Integration Tests:**
```bash
export TRIAGENT_SANDBOX_API_KEY="your-sandbox-api-key"
export TRIAGENT_SESSION_POOL_ENDPOINT="https://eastus.dynamicsessions.io/..."
az login
pytest tests/azure/ -v --tb=short
```

### 7.4 App Service Staging Slot Testing

**Purpose:** Test changes in a staging environment before swapping to production.

```bash
# Create staging slot
az webapp deployment slot create \
    --name triagent-sandbox-app \
    --resource-group triagent-sandbox-rg \
    --slot staging

# Deploy to staging
az webapp deploy --name triagent-sandbox-app --resource-group triagent-sandbox-rg \
    --slot staging --src-path app.zip --type zip

# Test staging
curl https://triagent-sandbox-app-staging.azurewebsites.net/health

# Run tests against staging
TRIAGENT_SANDBOX_URL=https://triagent-sandbox-app-staging.azurewebsites.net pytest tests/azure/ -v

# Swap to production
az webapp deployment slot swap \
    --name triagent-sandbox-app \
    --resource-group triagent-sandbox-rg \
    --slot staging --target-slot production
```

### 7.5 GitHub Actions Integration Test Workflow

**File:** `.github/workflows/integration-tests.yml`

```yaml
name: Integration Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  local-integration:
    name: Local Integration Tests (Testcontainers)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install uv && uv pip install --system -e ".[dev,test-integration]"
      - run: pytest tests/integration/ -v --tb=short

  azure-integration:
    name: Azure Sandbox Integration Tests
    runs-on: ubuntu-latest
    needs: local-integration
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      - run: pip install uv && uv pip install --system -e ".[dev,test-integration]"
      - run: ./scripts/deploy-sandbox.sh --slot staging
      - run: pytest tests/azure/ -v --tb=short
        env:
          TRIAGENT_SANDBOX_URL: https://triagent-sandbox-app-staging.azurewebsites.net
          TRIAGENT_SANDBOX_API_KEY: ${{ secrets.TRIAGENT_SANDBOX_API_KEY }}
      - run: |
          az webapp deployment slot swap \
            --name triagent-sandbox-app \
            --resource-group triagent-sandbox-rg \
            --slot staging --target-slot production
        if: success()
```

### 7.6 Docker Compose for Local Full-Stack Testing

**File:** `docker-compose.integration.yml`

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  fastapi:
    build:
      context: .
      dockerfile: Dockerfile.chainlit
    ports:
      - "8000:8000"
    environment:
      - TRIAGENT_REDIS_HOST=redis
      - TRIAGENT_REDIS_PORT=6379
      - TRIAGENT_REDIS_SSL=false
      - TRIAGENT_TRIAGENT_API_KEY=local-test-key
    depends_on:
      redis:
        condition: service_healthy
    command: uvicorn triagent.web.app:app --host 0.0.0.0 --port 8000

  integration-tests:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - TRIAGENT_SANDBOX_URL=http://fastapi:8000
      - TRIAGENT_SANDBOX_API_KEY=local-test-key
    depends_on:
      - fastapi
    command: pytest tests/integration/ tests/azure/test_sandbox_api.py -v
    profiles:
      - test
```

**Run Full-Stack Integration:**
```bash
docker compose -f docker-compose.integration.yml up -d redis fastapi
sleep 10
docker compose -f docker-compose.integration.yml run integration-tests
docker compose -f docker-compose.integration.yml down -v
```

### 7.7 Integration Test Summary

| Test Type | Command | Requirements |
|-----------|---------|--------------|
| Unit Tests | `pytest tests/web/ -v` | None |
| Local Integration | `pytest tests/integration/ -v` | Docker running |
| Docker Full-Stack | `docker compose -f docker-compose.integration.yml run integration-tests` | Docker running |
| Azure Sandbox | `pytest tests/azure/ -v` | Azure CLI auth, env vars |
| Staging Slot | Set `TRIAGENT_SANDBOX_URL` to staging | Staging slot created |
| E2E Browser | `pytest tests/e2e/ -v --browser chromium` | Server running |

### 7.8 Files to Create for Integration Testing

| File | Purpose |
|------|---------|
| `tests/integration/__init__.py` | Package init |
| `tests/integration/conftest.py` | Testcontainers fixtures |
| `tests/integration/test_redis_integration.py` | Redis session store tests |
| `tests/integration/test_api_integration.py` | FastAPI with Redis tests |
| `tests/azure/__init__.py` | Package init |
| `tests/azure/conftest.py` | Azure sandbox fixtures |
| `tests/azure/test_sandbox_api.py` | App Service API tests |
| `tests/azure/test_session_pool_api.py` | Session Pool direct tests |
| `scripts/deploy-sandbox.sh` | Sandbox deployment script |
| `docker-compose.integration.yml` | Local full-stack testing |
| `.github/workflows/integration-tests.yml` | CI/CD integration tests |

---

## Files to Create/Modify

| Phase | File | Action |
|-------|------|--------|
| 1 | `pyproject.toml` | **Modify** |
| 1 | `src/triagent/web/__init__.py` | Create |
| 1 | `src/triagent/web/routers/__init__.py` | Create |
| 1 | `src/triagent/web/services/__init__.py` | Create |
| 1 | `src/triagent/web/container/__init__.py` | Create |
| 2 | `src/triagent/web/config.py` | Create |
| 2 | `src/triagent/web/models.py` | Create |
| 2 | `src/triagent/web/auth.py` | Create |
| 2 | `src/triagent/web/app.py` | Create |
| 2 | `src/triagent/web/routers/session.py` | Create |
| 2 | `src/triagent/web/routers/chat.py` | Create |
| 2 | `src/triagent/web/routers/auth.py` | Create |
| 2 | `src/triagent/web/routers/health.py` | Create |
| 2 | `src/triagent/web/services/session_store.py` | Create |
| 2 | `src/triagent/web/services/session_proxy.py` | Create |
| 3 | `src/triagent/web/container/.chainlit/config.toml` | Create |
| 3 | `src/triagent/web/container/chainlit_app.py` | Create |
| 3 | `src/triagent/web/container/handlers.py` | Create |
| 3 | `src/triagent/web/container/api.py` | Create |
| 3 | `src/triagent/web/container/start.sh` | Create |
| 4 | `Dockerfile.chainlit` | Create |
| 4 | `.dockerignore` | **Modify** |
| 5 | `tests/web/__init__.py` | Create |
| 5 | `tests/web/conftest.py` | Create |
| 5 | `tests/web/test_auth.py` | Create |
| 5 | `tests/web/test_models.py` | Create |
| 5 | `tests/web/test_api.py` | Create |
| 6 | `tests/e2e/test_web_ui.py` | Create |

**Total: 28 files** (4 modify, 24 create)

---

## Verification Commands

```bash
# Phase 1: Dependencies
uv pip install -e ".[web,test-web]"
python -c "import chainlit; import fastapi; print('OK')"

# Phase 2: FastAPI Backend
uvicorn triagent.web.app:app --reload --port 8000
curl http://localhost:8000/health

# Phase 3: Chainlit
chainlit run src/triagent/web/container/chainlit_app.py --port 8080

# Phase 4: Container
docker build -f Dockerfile.chainlit -t ghcr.io/sdandey/triagent-chainlit:latest .
docker run -p 8080:8080 ghcr.io/sdandey/triagent-chainlit:latest

# Phase 5: Unit tests
pytest tests/web/ -v

# Phase 6: E2E tests
pytest tests/e2e/test_web_ui.py -v --browser chromium
```

---

## Key Reusable Code

**From existing codebase:**
- `sdk_client.py:create_sdk_client()` - Build agent options
- `config.py:ConfigManager` - Load/save credentials
- `hooks.py:get_triagent_hooks()` - Security hooks
- `prompts/system.py:get_system_prompt()` - Team-specific prompts

**Pattern to follow (from cli.py):**
```python
async with ClaudeSDKClient(options=options) as client:
    await client.query(prompt=user_input)
    async for msg in client.receive_response():
        process_sdk_message(msg)
```

---

## Notes

1. **Reuse existing code:** `sdk_client.py`, `config.py`, `hooks.py`, `prompts/`
2. **Infrastructure ready:** Session Pool, Redis, App Service (Bicep deployed)
3. **Container Registry:** GitHub Container Registry (ghcr.io)
4. **Test locally first:** FastAPI + Chainlit before containerizing
5. **API Providers:** Only `azure_foundry` (default) and `anthropic` - no Databricks

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-30 | sdandey | Initial implementation plan |
| 2.0 | 2025-12-30 | sdandey | Updated for PR #19: removed Databricks, added full code snippets, GHCR registry |
| 2.1 | 2025-12-30 | sdandey | Added Phase 7: Integration Testing Strategy with testcontainers, Azure sandbox, staging slots |
