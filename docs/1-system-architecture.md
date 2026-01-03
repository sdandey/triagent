# Triagent Web UI - System Architecture

**Document Version:** 1.4
**Prepared by:** sdandey
**Last Updated:** 2025-12-30
**Status:** Approved

## Table of Contents

1. [Overview](#overview)
   - [Key Components](#key-components)
   - [Authentication Layers](#authentication-layers)
2. [Component Architecture](#component-architecture)
3. [UI Components](#ui-components)
4. [Backend API Endpoints](#backend-api-endpoints)
5. [External Azure APIs](#external-azure-apis-session-pool)
6. [Container Internal APIs](#container-internal-apis)
7. [Sequence Diagrams](#sequence-diagrams)
8. [Data Models](#data-models)
9. [Conversation History](#conversation-history)

---

## Overview

This document defines the system architecture for the Triagent Web UI, a web-based chat interface for Azure DevOps automation using Claude AI. Users interact through a browser, with requests proxied to isolated container sandboxes running the triagent agent.

### Key Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web UI** | Chainlit | Chat interface with tool visualization |
| **Backend API** | FastAPI (App Service) | Session management, request routing |
| **Session Store** | Azure Redis Cache | User-session mapping, metadata |
| **Sandbox** | Container Apps Session Pool | Isolated execution environment |
| **LLM Provider** | Azure Foundry/Anthropic | Claude AI inference |

### Authentication Layers

The system uses **two separate authentication mechanisms** at different layers:

:::mermaid
flowchart LR
    subgraph Layer1["Layer 1: Backend Auth"]
        Browser["Browser"]
        AppService["App Service"]
    end

    subgraph Layer2["Layer 2: LLM Auth"]
        Container["Container"]
        LLM["Claude Provider"]
    end

    Browser -->|"Triagent API Key"| AppService
    AppService -->|"Creates session"| Container
    Container -->|"API Token"| LLM
:::

| Key | Purpose | Scope | Example |
|-----|---------|-------|---------|
| **Triagent API Key** | Authenticates user to Triagent backend | Shared among authorized team members | `triagent-sandbox-2025-key` |
| **API Token** | Authenticates to Claude LLM provider | Personal per user/workspace | Azure AD token (Foundry) or `sk-ant-...` (Anthropic) |

**Triagent API Key (MVP Authentication):**
- Stored in App Service environment variable: `TRIAGENT_API_KEY`
- User enters in Setup Wizard form
- Backend validates before creating session
- Shared secret for authorized team access (simpler than Azure AD for MVP)

**API Token (Claude Provider):**
- User's personal token for their LLM provider
- Passed to container via `/init` endpoint
- Used by triagent agent to call Claude API
- Provider-specific format:
  - Azure Foundry: Azure AD token or API key
  - Anthropic: `sk-ant-api03-xxxxx`

---

## Component Architecture

### High-Level Architecture

:::mermaid
flowchart TB
    subgraph Browser["User's Browser"]
        UI["Chainlit Web UI<br/>- Chat Messages<br/>- Tool Cards<br/>- Setup Wizard"]
    end

    subgraph AppService["Azure App Service"]
        API["FastAPI Backend"]
        Auth["Auth Middleware<br/>API Key Validation"]
        SS["SessionService<br/>create/get/delete"]
        SP["SessionProxy<br/>HTTP + SSE"]
        Store["SessionStore<br/>Redis Client"]
    end

    subgraph Redis["Azure Cache for Redis"]
        SM["Session Metadata<br/>TTL: 2 hours"]
    end

    subgraph SessionPool["Azure Container Apps Session Pool"]
        subgraph Container1["Session Container - User A"]
            CL1["Chainlit App<br/>@cl.on_message<br/>@cl.step"]
            AG1["Triagent Agent<br/>Tool Loop"]
            Tools1["Tool Executors<br/>Azure CLI - MCP"]
        end
        subgraph Container2["Session Container - User B"]
            CL2["..."]
        end
    end

    subgraph LLM["LLM Provider"]
        AZ["Azure Foundry"]
        AN["Anthropic API"]
    end

    UI -->|"HTTPS/WebSocket"| API
    API --> Auth
    Auth --> SS
    Auth --> SP
    SS --> Store
    Store -->|"Redis Protocol (SSL)"| SM
    SP -->|"HTTPS + Bearer Token"| Container1
    CL1 --> AG1
    AG1 --> Tools1
    AG1 -->|"HTTPS"| AZ
    AG1 -->|"HTTPS"| AN
:::

### Detailed Component View

:::mermaid
flowchart LR
    subgraph Client["Browser Layer"]
        direction TB
        Chat["Chat Interface"]
        ToolUI["Tool Execution Cards"]
        Wizard["Setup Wizard"]
        AuthUI["Azure Auth Modal"]
    end

    subgraph Gateway["API Gateway Layer"]
        direction TB
        CORS["CORS Handler"]
        RateLimit["Rate Limiter"]
        APIKey["API Key Middleware"]
        Router["Request Router"]
    end

    subgraph Services["Service Layer"]
        direction TB
        SessionSvc["SessionService"]
        ChatSvc["ChatService"]
        AuthSvc["AuthService"]
        HealthSvc["HealthService"]
    end

    subgraph Infrastructure["Infrastructure Layer"]
        direction TB
        SessionMgr["SessionManager<br/>Azure Sessions API"]
        SessionStore["SessionStore<br/>Redis Operations"]
        Proxy["SessionProxy<br/>HTTP/SSE Proxy"]
    end

    Client --> Gateway
    Gateway --> Services
    Services --> Infrastructure
:::

---

## UI Components

The Chainlit web interface consists of four main components that users interact with.

### UI State Flow

:::mermaid
stateDiagram-v2
    [*] --> CheckSession: User opens web UI

    CheckSession --> SetupWizard: No session exists
    CheckSession --> ChatInterface: Session exists

    SetupWizard --> CreatingSession: Submit form
    CreatingSession --> AuthModal: Session created
    CreatingSession --> SetupWizard: Error

    AuthModal --> CheckingAuth: User completes device code
    CheckingAuth --> ChatInterface: Authenticated
    CheckingAuth --> AuthModal: Not yet authenticated

    ChatInterface --> ToolCard: Agent executes tool
    ToolCard --> ChatInterface: Tool complete

    ChatInterface --> [*]: Session expires
:::

---

### 1. Setup Wizard

**Purpose:** Initial configuration form displayed when no active session exists.

**When Shown:** User opens web UI and no session is found in Redis.

**Form Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Email | text input | Yes | User's email for session ID generation |
| API Key | password | Yes | Shared triagent API key |
| Team | dropdown | Yes | `levvia`, `omnia`, `omnia-data` |
| API Provider | dropdown | Yes | `azure_foundry`, `anthropic` |
| API Base URL | text input | Conditional | Required for Azure Foundry |
| API Token | password | Yes | Claude API token |

**Wireframe:**

```
┌─────────────────────────────────────────────────────────────┐
│                  TRIAGENT SESSION SETUP                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Email Address                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ user@example.com                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  API Key                                                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ ••••••••••••••••••••••••                             │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Team                              API Provider              │
│  ┌──────────────────────┐         ┌──────────────────────┐  │
│  │ Omnia Data        ▼  │         │ Azure Foundry     ▼  │  │
│  └──────────────────────┘         └──────────────────────┘  │
│                                                              │
│  API Base URL                                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ https://foundry.azure.com/api/v1/claude-endpoint     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  API Token                                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ ••••••••••••••••••••••••••••••••                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│                    ┌─────────────────────┐                   │
│                    │   Create Session    │                   │
│                    └─────────────────────┘                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Flow:**
1. User fills in all required fields
2. Clicks "Create Session"
3. Backend validates API key
4. Container session provisioned
5. Wizard disappears → Auth Modal appears

---

### 2. Auth Modal

**Purpose:** Display Azure CLI device code for authentication.

**When Shown:** After session creation, before user can use Azure DevOps features.

**Contents:**

| Element | Description |
|---------|-------------|
| Device Code | 8-character code (e.g., `ABCD-EFGH`) |
| Verification URL | `https://microsoft.com/devicelogin` |
| Instructions | Step-by-step guide |
| Status | Checking/Authenticated indicator |

**Wireframe:**

```
┌─────────────────────────────────────────────────────────────┐
│              AZURE AUTHENTICATION REQUIRED                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  To use Azure DevOps tools, please authenticate:             │
│                                                              │
│  1. Open this URL in a new tab:                              │
│     ┌─────────────────────────────────────────────────┐     │
│     │  https://microsoft.com/devicelogin    [Copy]    │     │
│     └─────────────────────────────────────────────────┘     │
│                                                              │
│  2. Enter this code:                                         │
│                                                              │
│              ┌─────────────────────┐                         │
│              │     ABCD-EFGH       │                         │
│              └─────────────────────┘                         │
│                                                              │
│  3. Sign in with your Microsoft account                      │
│                                                              │
│  ────────────────────────────────────────────────────────   │
│                                                              │
│  Status: ⏳ Waiting for authentication...                    │
│                                                              │
│  ┌────────────────────┐     ┌────────────────────┐          │
│  │   Open Login URL   │     │  I've Authenticated │          │
│  └────────────────────┘     └────────────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Flow:**
1. Modal displays device code from container
2. User opens verification URL in new tab
3. User enters code and signs in
4. User clicks "I've Authenticated"
5. Backend polls `/api/auth/azure/status`
6. If authenticated → Modal closes, chat enabled
7. If not → Show "Not yet authenticated" message

---

### 3. Tool Cards

**Purpose:** Visual representation of tool execution in the chat interface.

**When Shown:** When the AI agent calls a tool (Azure CLI, MCP server, etc.).

**Implementation:** Chainlit `@cl.step(type="tool")` decorator automatically creates these cards.

**Card Contents:**

| Element | Description |
|---------|-------------|
| Icon | Tool type indicator (🔧 for CLI, 📊 for query) |
| Name | Tool name (e.g., "Azure CLI", "Kusto Query") |
| Input | Command or query being executed |
| Output | Execution result (collapsible for long output) |
| Duration | Execution time in seconds |
| Status | Success/Error indicator |

**Wireframe:**

```
┌─────────────────────────────────────────────────────────────┐
│ 🔧 Azure CLI                                    ▼ Collapse  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input:                                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ az repos pr list --repository cortex-ui --status    │    │
│  │ active --output json                                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Output:                                                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ [                                                    │    │
│  │   {                                                  │    │
│  │     "pullRequestId": 1234,                          │    │
│  │     "title": "Add user authentication",             │    │
│  │     "status": "active",                             │    │
│  │     "createdBy": "user@example.com"                 │    │
│  │   }                                                  │    │
│  │ ]                                                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ✅ Success                                      2.5s        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Chainlit Code:**
```python
@cl.step(type="tool", name="Azure CLI")
async def execute_azure_cli(command: str):
    """Execute Azure CLI command - automatically creates tool card."""
    # Input is automatically captured from function arguments
    result = await run_in_sandbox(command)
    # Return value becomes the output displayed in the card
    return result.stdout
```

**Collapsed State:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🔧 Azure CLI                           ✅ 2.5s   ▶ Expand   │
└─────────────────────────────────────────────────────────────┘
```

---

### 4. Chat Interface

**Purpose:** Main conversation interface for interacting with the AI agent.

**When Shown:** After successful session creation and authentication.

**Components:**

| Element | Description |
|---------|-------------|
| Message History | Scrollable list of user/assistant messages |
| Tool Cards | Inline tool execution cards (see above) |
| Streaming Indicator | Shows when AI is generating response |
| Input Area | Text input with send button |
| Slash Commands | Quick actions (`/clear`, `/team`, `/help`) |

**Wireframe:**

```
┌─────────────────────────────────────────────────────────────┐
│  TRIAGENT                           Team: Omnia Data   [⚙]  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 👤 Show me open PRs in the cortex-ui repository      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 🤖 I'll fetch the open pull requests for cortex-ui. │    │
│  │                                                      │    │
│  │ ┌─────────────────────────────────────────────────┐ │    │
│  │ │ 🔧 Azure CLI                    ✅ 2.5s  ▶      │ │    │
│  │ └─────────────────────────────────────────────────┘ │    │
│  │                                                      │    │
│  │ Here are the **3 open PRs** in cortex-ui:           │    │
│  │                                                      │    │
│  │ | ID   | Title              | Author    | Status  | │    │
│  │ |------|--------------------|-----------|---------| │    │
│  │ | 1234 | Add authentication | user@...  | Active  | │    │
│  │ | 1235 | Fix build error    | dev@...   | Active  | │    │
│  │ | 1236 | Update README      | admin@... | Active  | │    │
│  │                                                      │    │
│  │ Would you like me to review any of these PRs?       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ═══════════════════════════════════════════════════════    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Type a message...                           [Send]  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  💡 Try: /clear, /team, /help                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Streaming Response:**
When the AI is generating a response, text appears character-by-character:

```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 I'll analyze the build failure in pipeline 5678...       │
│                                                    ▌        │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend API Endpoints

The FastAPI backend exposes 6 MVP endpoints.

### Endpoint Summary

| # | Method | Endpoint | Purpose |
|---|--------|----------|---------|
| 1 | `GET` | `/health` | Health check |
| 2 | `POST` | `/api/session` | Create session |
| 3 | `GET` | `/api/session` | Get session status |
| 4 | `POST` | `/api/chat/stream` | Send message (SSE) |
| 5 | `POST` | `/api/auth/azure` | Start Azure device code |
| 6 | `GET` | `/api/auth/azure/status` | Check Azure auth |

---

### 1. Health Check

```
GET /health
```

**Purpose:** Kubernetes/App Service health probe

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-30T12:00:00Z",
  "version": "1.0.0"
}
```

| Status | Description |
|--------|-------------|
| 200 | Service healthy |
| 503 | Service unhealthy |

---

### 2. Create Session

```
POST /api/session
```

**Purpose:** Create a new user session and provision container sandbox

**Request:**
```json
{
  "email": "user@example.com",
  "api_key": "triagent-api-key-here",
  "team": "omnia-data",
  "api_provider": "azure_foundry",
  "api_base_url": "https://foundry.azure.com/api/v1/claude-endpoint",
  "api_token": "azure-ad-token..."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's email address |
| api_key | string | Yes | Shared API key for authorization |
| team | enum | Yes | `levvia`, `omnia`, `omnia-data` |
| api_provider | enum | Yes | `azure_foundry`, `anthropic` |
| api_base_url | string | Conditional | Required for azure_foundry |
| api_token | string | Yes | Claude API token |

**Response (201 Created):**
```json
{
  "session_id": "triagent-a1b2c3d4e5f67890",
  "email": "user@example.com",
  "team": "omnia-data",
  "created_at": "2025-12-30T12:00:00Z",
  "expires_at": "2025-12-30T14:00:00Z",
  "container_status": "ready"
}
```

**Errors:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | INVALID_REQUEST | Missing or invalid fields |
| 401 | INVALID_API_KEY | API key validation failed |
| 409 | SESSION_EXISTS | Session already exists for user |
| 500 | CONTAINER_ERROR | Failed to provision container |

---

### 3. Get Session

```
GET /api/session
```

**Purpose:** Retrieve current session metadata

**Request Headers:**
```
X-Session-ID: triagent-a1b2c3d4e5f67890
```

**Response (200 OK):**
```json
{
  "session_id": "triagent-a1b2c3d4e5f67890",
  "email": "user@example.com",
  "team": "omnia-data",
  "api_provider": "azure_foundry",
  "created_at": "2025-12-30T12:00:00Z",
  "last_active": "2025-12-30T12:30:00Z",
  "azure_authenticated": true,
  "container_status": "running"
}
```

**Errors:**

| Status | Code | Description |
|--------|------|-------------|
| 404 | SESSION_NOT_FOUND | Session not found or expired |

---

### 4. Send Chat Message (Streaming)

```
POST /api/chat/stream
```

**Purpose:** Send a message and receive streaming response via SSE

**Request Headers:**
```
Content-Type: application/json
Accept: text/event-stream
X-Session-ID: triagent-a1b2c3d4e5f67890
```

**Request:**
```json
{
  "message": "Show me open PRs in cortex-ui repository"
}
```

**Response:** Server-Sent Events stream

```
event: message_start
data: {"type": "message_start", "message_id": "msg-123"}

event: content_block_delta
data: {"type": "content_block_delta", "delta": {"text": "I'll fetch "}}

event: content_block_delta
data: {"type": "content_block_delta", "delta": {"text": "the open PRs..."}}

event: tool_use_start
data: {"type": "tool_use_start", "tool_id": "tool-1", "name": "azure_cli", "input": "az repos pr list --repository cortex-ui --status active"}

event: tool_use_output
data: {"type": "tool_use_output", "tool_id": "tool-1", "output": "[{\"pullRequestId\": 1234}]"}

event: message_stop
data: {"type": "message_stop", "stop_reason": "end_turn"}
```

**SSE Event Types:**

| Event | Description |
|-------|-------------|
| `message_start` | Message processing started |
| `content_block_delta` | Incremental text content |
| `tool_use_start` | Tool execution beginning (shows input) |
| `tool_use_output` | Tool execution result |
| `message_stop` | Message complete |
| `error` | Error occurred |

---

### 5. Start Azure Authentication

```
POST /api/auth/azure
```

**Purpose:** Initiate Azure CLI device code authentication flow

**Request Headers:**
```
X-Session-ID: triagent-a1b2c3d4e5f67890
```

**Response (200 OK):**
```json
{
  "device_code": "ABCD-EFGH",
  "verification_url": "https://microsoft.com/devicelogin",
  "expires_in": 900,
  "message": "Open the URL and enter the code to authenticate with Azure"
}
```

---

### 6. Check Azure Authentication Status

```
GET /api/auth/azure/status
```

**Purpose:** Check if Azure CLI authentication completed

**Request Headers:**
```
X-Session-ID: triagent-a1b2c3d4e5f67890
```

**Response (200 OK) - Authenticated:**
```json
{
  "authenticated": true,
  "user": "user@example.com",
  "subscription": "My Subscription",
  "tenant": "contoso.onmicrosoft.com"
}
```

**Response (200 OK) - Not Authenticated:**
```json
{
  "authenticated": false,
  "message": "Azure authentication not completed"
}
```

---

## External Azure APIs (Session Pool)

The FastAPI backend communicates with Azure Container Apps Session Pool using these APIs.

### Authentication

All requests require:
- **Authorization:** `Bearer {entra_token}`
- **Identifier:** `{session_id}` (4-128 characters)

**Token Scope:** `https://dynamicsessions.io/.default`

### API Endpoints (MVP)

| API | Method | Endpoint | Purpose |
|-----|--------|----------|---------|
| Execute Code | `POST` | `{pool_endpoint}/code/execute` | Run code/commands in session |

> **MVP Scope:** Only the Execute Code API is required. File upload/download APIs (`/files/*`) are available in the Session Pool but not used in the initial implementation. The chat interface communicates via text messages and SSE streaming - no file transfer needed.

---

### Execute Code

```
POST {pool_endpoint}/code/execute
```

**Request Headers:**
```
Authorization: Bearer {entra_token}
Identifier: triagent-a1b2c3d4e5f67890
Content-Type: application/json
```

**Request:**
```json
{
  "properties": {
    "codeInputType": "inline",
    "executionType": "synchronous",
    "code": "print('Hello from sandbox')"
  }
}
```

**Response:**
```json
{
  "properties": {
    "status": "Success",
    "stdout": "Hello from sandbox\n",
    "stderr": "",
    "executionResult": null,
    "executionTimeInMilliseconds": 150
  }
}
```

### Future Enhancement: File APIs

When file transfer capabilities are needed, the following Session Pool APIs are available:

| API | Method | Endpoint | Use Case |
|-----|--------|----------|----------|
| Upload File | `POST` | `{pool}/files/upload` | Upload JSON/CSV for analysis |
| List Files | `GET` | `{pool}/files` | Browse session files |
| Download File | `GET` | `{pool}/files/content/{name}` | Export reports/data |

---

## Container Internal APIs

These endpoints run inside the session container and are called by the FastAPI backend via the Session Pool proxy.

### Endpoint Summary

| # | Method | Endpoint | Purpose |
|---|--------|----------|---------|
| 1 | `POST` | `/init` | Initialize triagent config |
| 2 | `POST` | `/chat` | Process message (non-streaming) |
| 3 | `POST` | `/chat/stream` | Stream response (SSE) |
| 4 | `POST` | `/auth/azure` | Start device code flow |
| 5 | `GET` | `/auth/azure/status` | Check auth status |
| 6 | `GET` | `/config` | Get current config |
| 7 | `GET` | `/health` | Container health |

---

### C1. Initialize Session

```
POST /init
```

**Request:**
```json
{
  "api_provider": "azure_foundry",
  "api_base_url": "https://foundry.azure.com/api/v1/claude-endpoint",
  "api_token": "azure-ad-token...",
  "team": "omnia-data"
}
```

**Response:**
```json
{
  "status": "initialized",
  "team": "omnia-data",
  "api_provider": "azure_foundry"
}
```

---

### C2. Process Chat Message

```
POST /chat
```

**Request:**
```json
{
  "message": "Show me recent exceptions in DataKitchenService"
}
```

**Response:**
```json
{
  "response": "I'll query the Application Insights logs...",
  "tool_calls": [
    {
      "id": "tool-1",
      "name": "azure_cli",
      "input": "az monitor app-insights query --app ...",
      "output": "[{\"timestamp\": \"...\", \"exception\": \"...\"}]",
      "duration_ms": 3200
    }
  ]
}
```

---

### C3. Stream Chat Message

```
POST /chat/stream
```

**Request:**
```json
{
  "message": "Debug the failing unit test"
}
```

**Response:** SSE stream (same format as `/api/chat/stream`)

---

### C4-C7. Auth & Config Endpoints

Same request/response format as the corresponding backend APIs.

---

## Sequence Diagrams

### 1. Session Creation Flow

:::mermaid
sequenceDiagram
    participant B as Browser
    participant F as FastAPI Backend
    participant R as Redis
    participant S as Session Pool API
    participant C as Container

    B->>F: POST /api/session
    Note over B,F: {email, api_key, team, api_provider, api_token}

    F->>F: Validate API key
    F->>F: Generate session_id = sha256(email)[:16]

    F->>R: Check existing session
    R-->>F: Not found

    F->>F: Get Entra token (scope: dynamicsessions.io)

    F->>S: POST /code/execute
    Note over F,S: Header: Identifier={session_id}

    S->>C: Create container (if new)
    S->>C: Execute init code

    C-->>S: Container ready
    S-->>F: Execution result

    F->>R: Store session metadata (TTL: 2hr)

    F-->>B: 201 Created
    Note over F,B: {session_id, team, expires_at}
:::

---

### 2. Chat Message Flow (Streaming)

:::mermaid
sequenceDiagram
    participant B as Browser
    participant F as FastAPI Backend
    participant R as Redis
    participant S as Session Pool API
    participant C as Container
    participant L as LLM Provider

    B->>F: POST /api/chat/stream
    Note over B,F: Header: X-Session-ID

    F->>R: Validate session exists
    R-->>F: Session metadata

    F->>R: Update last_active

    F->>S: Proxy POST /chat/stream
    Note over F,S: SSE connection

    S->>C: Forward request
    C->>L: Send message + tools

    loop Streaming Response
        L-->>C: Token delta
        C-->>S: SSE: content_block_delta
        S-->>F: Forward SSE
        F-->>B: SSE: content_block_delta
    end

    alt Tool Call Required
        L-->>C: Tool use request
        C-->>S: SSE: tool_use_start
        S-->>F: Forward SSE
        F-->>B: SSE: tool_use_start

        C->>C: Execute tool (Azure CLI)

        C-->>S: SSE: tool_use_output
        S-->>F: Forward SSE
        F-->>B: SSE: tool_use_output

        C->>L: Tool result
        L-->>C: Continue response
    end

    L-->>C: End turn
    C-->>S: SSE: message_stop
    S-->>F: Forward SSE
    F-->>B: SSE: message_stop
:::

---

### 3. Azure Authentication Flow

:::mermaid
sequenceDiagram
    participant B as Browser
    participant F as FastAPI Backend
    participant S as Session Pool API
    participant C as Container
    participant AZ as Azure AD

    B->>F: POST /api/auth/azure
    Note over B,F: Header: X-Session-ID

    F->>S: Proxy POST /auth/azure
    S->>C: Forward request

    C->>C: az login --use-device-code
    C->>AZ: Request device code
    AZ-->>C: Device code + URL

    C-->>S: {device_code, verification_url}
    S-->>F: Forward response
    F-->>B: {device_code: "ABCD-EFGH", url: "..."}

    Note over B: User opens URL in new tab
    B->>AZ: Enter device code
    AZ->>AZ: Authenticate user
    AZ-->>B: Success page

    B->>F: GET /api/auth/azure/status
    F->>S: Proxy GET /auth/azure/status
    S->>C: Forward request

    C->>C: az account show
    C-->>S: {authenticated: true, user: "..."}
    S-->>F: Forward response
    F-->>B: {authenticated: true}

    B->>B: Enable chat interface
:::

---

### 4. Tool Execution Flow

:::mermaid
sequenceDiagram
    participant CL as Chainlit App
    participant AG as Triagent Agent
    participant L as LLM Provider
    participant T as Tool Executor
    participant AZ as Azure DevOps

    CL->>AG: User message
    AG->>L: Send message + tool schemas

    L->>L: Analyze request
    L-->>AG: Tool call: azure_cli
    Note over L,AG: {name: "azure_cli", input: "az repos pr list..."}

    AG->>AG: @cl.step(type="tool") decorator

    rect rgb(240, 240, 255)
        Note over AG,AZ: Tool Execution (visible in UI)
        AG->>T: Execute azure_cli
        T->>AZ: az repos pr list --status active
        AZ-->>T: PR data JSON
        T-->>AG: Tool output
    end

    AG->>AG: step.output = result

    AG->>L: Tool result
    L->>L: Generate response
    L-->>AG: Text response

    AG-->>CL: Stream response + tool card
:::

---

## Data Models

### Session Metadata (Redis)

**Key:** `session:user:{email}`
**TTL:** 7200 seconds (2 hours)

```json
{
  "session_id": "triagent-a1b2c3d4e5f67890",
  "email": "user@example.com",
  "team": "omnia-data",
  "api_provider": "azure_foundry",
  "created_at": "2025-12-30T12:00:00Z",
  "last_active": "2025-12-30T12:30:00Z",
  "azure_authenticated": true,
  "container_status": "running"
}
```

---

### Error Response

```json
{
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "No active session found for the provided session ID",
    "details": {
      "session_id": "triagent-invalid"
    }
  }
}
```

**Error Codes:**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_REQUEST | 400 | Missing or invalid fields |
| INVALID_API_KEY | 401 | API key validation failed |
| SESSION_NOT_FOUND | 404 | Session not found or expired |
| SESSION_EXISTS | 409 | Session already exists |
| CONTAINER_ERROR | 500 | Container provisioning failed |

---

### Tool Call

```json
{
  "id": "tool-abc123",
  "name": "azure_cli",
  "input": "az repos pr list --status active",
  "output": "[{\"pullRequestId\": 1234}]",
  "status": "success",
  "duration_ms": 2500
}
```

---

### SSE Event

```json
{
  "type": "content_block_delta",
  "index": 0,
  "delta": {
    "type": "text_delta",
    "text": "Here are the results..."
  }
}
```

---

## Conversation History

### Storage Strategy

**Method:** Container memory via Chainlit `cl.chat_context`

| Aspect | Detail |
|--------|--------|
| **Storage Location** | In-container memory |
| **Persistence** | Session lifetime only (max 2 hours) |
| **LLM Integration** | `cl.chat_context.to_openai()` |
| **External Persistence** | None (MVP) |

### How It Works

:::mermaid
flowchart LR
    subgraph Container["Session Container"]
        direction TB
        CL["Chainlit App"]
        CTX["cl.chat_context<br/>Auto-accumulates messages"]
        AG["Agent"]
        LLM["LLM Call"]
    end

    User -->|"Message"| CL
    CL -->|"Store"| CTX
    CTX -->|"to_openai()"| AG
    AG -->|"Full history"| LLM
    LLM -->|"Response"| CL
    CL -->|"Store"| CTX
:::

### Behavior

1. **On Message Received:** Chainlit automatically adds to `cl.chat_context`
2. **On LLM Call:** Agent converts context to OpenAI format
3. **On Session Expiry:** History is lost (container destroyed)
4. **On Browser Refresh:** History preserved (container still running)

### Future Enhancement

For persistent history, add Cosmos DB:
- Store conversations on message completion
- Retrieve on session reconnection
- Enable cross-session continuity

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-30 | sdandey | Initial system architecture with Mermaid diagrams |
| 1.1 | 2025-12-30 | sdandey | Simplified External Azure APIs - removed file APIs from MVP scope |
| 1.2 | 2025-12-30 | sdandey | Added UI Components section with wireframes for Setup Wizard, Auth Modal, Tool Cards, and Chat Interface |
| 1.3 | 2025-12-30 | sdandey | Added Authentication Layers section clarifying Triagent API Key vs API Token |
| 1.4 | 2025-12-30 | sdandey | Removed Databricks provider per PR #19; only azure_foundry and anthropic supported |
