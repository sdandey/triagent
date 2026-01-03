# ADR-001: Chat Interface Framework Selection

**Document Version:** 1.0
**Prepared by:** sdandey
**Last Updated:** 2025-12-30
**Status:** Accepted

## Table of Contents

1. [Context](#context)
2. [Decision](#decision)
3. [Options Considered](#options-considered)
4. [Comparison Matrix](#comparison-matrix)
5. [Deep-Dive: Chainlit vs Open WebUI](#deep-dive-chainlit-vs-open-webui)
6. [Consequences](#consequences)
7. [Risk Mitigation](#risk-mitigation)
8. [Sources](#sources)

---

## Context

### Problem Statement

The Triagent Web UI project requires a chat interface framework to build a web-based chat interface for Azure DevOps automation. The framework must support:

1. **Python-native development** - No frontend JavaScript/TypeScript code
2. **Tool execution visualization** - Show tool calls with inputs/outputs in the UI
3. **Real-time streaming** - WebSocket-based response streaming
4. **Session management** - Per-user session state persistence
5. **Sandbox log visualization** - Surface container sandbox logs alongside LLM responses
6. **Permissive license** - Apache 2.0 or similar for commercial use

### Constraints

- Must integrate with existing Python triagent codebase
- Must work with Azure Container Apps dynamic sessions
- Should minimize deployment complexity
- Team has limited frontend development resources

---

## Decision

**Selected Framework: Chainlit**

Chainlit was selected as the chat interface framework for the Triagent Web UI MVP.

### Rationale

1. **Native `@cl.step` decorator** - Provides first-class support for visualizing tool execution with input/output tracking, exactly matching our requirement to show sandbox logs
2. **Python-native** - Direct integration with triagent Python codebase without API translation layers
3. **Lighter deployment** - Embeds directly in App Service (FastAPI + Socket.IO)
4. **Active development** - v2.9.4 released December 2025, healthy release cadence
5. **MCP support** - Native Model Context Protocol integration for tool calling

### Important Note

As of **May 2025**, Chainlit became community-maintained. The original team stepped back to focus on a new startup. Despite this, the project continues to receive regular updates and security patches. Risk mitigation strategies are outlined below.

---

## Options Considered

### 1. Chainlit (Selected)

| Attribute | Value |
|-----------|-------|
| **GitHub Stars** | 11.3k |
| **Latest Version** | v2.9.4 (Dec 2025) |
| **License** | Apache 2.0 |
| **Maintenance** | Community-maintained |
| **Python-Native** | Yes |

**Pros:**
- Best-in-class tool execution UI with `@cl.step` decorator
- Native LangChain/LlamaIndex integration
- Built-in authentication (OAuth, Azure AD, custom headers)
- Session management via `cl.user_session`
- WebSocket streaming out of the box
- Prompt Playground for debugging

**Cons:**
- Community-maintained (uncertain long-term)
- Previous concerns about features moving to closed-source LiteralAI

---

### 2. Gradio

| Attribute | Value |
|-----------|-------|
| **GitHub Stars** | 41.1k |
| **Latest Version** | v6.2.0 (Dec 2025) |
| **License** | Apache 2.0 |
| **Maintenance** | Hugging Face backed |
| **Python-Native** | Yes |

**Pros:**
- Strong corporate backing (Hugging Face)
- Massive community (41k+ stars)
- `gr.ChatInterface` for quick chatbot UIs
- Native multimodal support
- Easy embedding on Hugging Face Spaces

**Cons:**
- Less sophisticated tool execution UI
- Session management less intuitive
- More suited for demos than complex conversational apps
- Limited customization for tool visualization

**Why Not Selected:** Lacks native support for the detailed tool execution visualization we require.

---

### 3. Open WebUI

| Attribute | Value |
|-----------|-------|
| **GitHub Stars** | 119k |
| **Latest Version** | v0.6.43 (Dec 2025) |
| **License** | MIT |
| **Maintenance** | Very active community |
| **Python-Native** | No (Docker application) |

**Pros:**
- Most popular open-source LLM UI (119k stars)
- Full ChatGPT-like experience
- Built-in RAG, web search, tools
- Enterprise features (RBAC, LDAP, SCIM 2.0)
- Voice/video calls

**Cons:**
- NOT a Python library - it's a complete Docker application
- Requires separate deployment
- Custom sandbox visualization needs Pipeline development
- OpenAI-compatible API wrapper required for integration

**Why Not Selected:** Architecture mismatch - would require separate deployment and API translation layer, increasing complexity significantly.

---

### 4. LobeChat

| Attribute | Value |
|-----------|-------|
| **GitHub Stars** | 69.6k |
| **Latest Version** | v2.0.0 (Dec 2025) |
| **License** | MIT |
| **Maintenance** | Active |
| **Python-Native** | No (TypeScript/Node.js) |

**Pros:**
- Beautiful modern UI
- MCP Marketplace integration
- Multi-provider support
- One-click deployment

**Cons:**
- TypeScript/Node.js - not Python-native
- Requires separate frontend deployment
- Would need API integration approach

**Why Not Selected:** Not Python-native, would require separate frontend codebase.

---

### 5. Panel (HoloViz)

| Attribute | Value |
|-----------|-------|
| **GitHub Stars** | 5.3k |
| **Latest Version** | v1.8.4 |
| **License** | BSD-3 |
| **Maintenance** | NumFOCUS/HoloViz backed |
| **Python-Native** | Yes |

**Pros:**
- Pure Python (NumFOCUS backed)
- `ChatInterface` and `ChatFeed` components
- Excellent for data visualization + chat
- LangChain integration

**Cons:**
- Less focused on chat (broader scope)
- Tool execution UI less polished
- Smaller chat-specific community

**Why Not Selected:** Tool execution visualization not as sophisticated as Chainlit.

---

### 6. Google Mesop

| Attribute | Value |
|-----------|-------|
| **GitHub Stars** | 6.3k |
| **Latest Version** | Latest |
| **License** | Apache 2.0 |
| **Maintenance** | Google backed |
| **Python-Native** | Yes |

**Pros:**
- Google-backed (strong support)
- Pure Python, no JS/CSS/HTML
- Cloud Run deployment integration

**Cons:**
- Newer framework, smaller ecosystem
- Less mature than alternatives
- Limited tool execution features

**Why Not Selected:** Limited tool execution visualization capabilities.

---

### 7. NiceGUI

| Attribute | Value |
|-----------|-------|
| **GitHub Stars** | 11.2k |
| **Latest Version** | Latest |
| **License** | MIT |
| **Maintenance** | Active |
| **Python-Native** | Yes |

**Pros:**
- Python wrapper around Vue/Quasar
- `ui.chat_message` component
- FastAPI-based backend
- Full web app capabilities

**Cons:**
- Less chat-focused
- Tool UI needs custom implementation
- Requires more setup for LLM integrations

**Why Not Selected:** Would require significant custom development for tool visualization.

---

## Comparison Matrix

| Framework | Stars | Python-Native | Tool UI | Session Mgmt | Corporate Backing | Sandbox Logs |
|-----------|-------|---------------|---------|--------------|-------------------|--------------|
| **Chainlit** | 11.3k | ✅ | ✅ Excellent | ✅ | ⚠️ Community | ✅ Native |
| Gradio | 41.1k | ✅ | ⚠️ Basic | ⚠️ | ✅ Hugging Face | ⚠️ Custom |
| Open WebUI | 119k | ❌ | ✅ Built-in | ✅ | ⚠️ Community | ⚠️ Pipeline |
| LobeChat | 69.6k | ❌ | ✅ Built-in | ✅ | ⚠️ Community | ❌ API wrap |
| Panel | 5.3k | ✅ | ⚠️ Basic | ✅ | ✅ HoloViz | ⚠️ Custom |
| Mesop | 6.3k | ✅ | ⚠️ Basic | ⚠️ | ✅ Google | ⚠️ Custom |
| NiceGUI | 11.2k | ✅ | ⚠️ Basic | ✅ | ⚠️ Community | ⚠️ Custom |

---

## Deep-Dive: Chainlit vs Open WebUI

### Architecture Comparison

| Aspect | Chainlit | Open WebUI |
|--------|----------|------------|
| **Type** | Python library/framework | Complete Docker application |
| **Backend** | FastAPI + Socket.IO | Python backend + Svelte frontend |
| **Deployment** | Embedded in your app | Separate deployment |
| **Integration** | Direct Python code | API + Pipelines |
| **Customization** | Full code control | Tools/Functions/Pipelines |

### Sandbox Log Visualization

#### Chainlit

```python
@cl.step(type="tool", name="Azure CLI")
async def execute_azure_cli(command: str):
    """Execute Azure CLI command in sandbox and show output."""
    result = await container_session.execute(command)
    return result.stdout  # Automatically shown in UI

@cl.on_message
async def handle_message(message: cl.Message):
    async with cl.Step(name="Executing in Sandbox") as step:
        step.input = f"Running: {command}"
        output = await execute_azure_cli(command)
        step.output = output

    await cl.Message(content=f"Command output:\n```\n{output}\n```").send()
```

**Key Features:**
- `@cl.step(type="tool")` decorator auto-visualizes execution
- Input/output tracked and displayed in UI
- Steps are collapsible (users can expand for details)
- Real-time streaming during execution

#### Open WebUI

Open WebUI would require:
1. Custom Pipeline implementation
2. "Backend-Controlled, UI-Compatible Flow" pattern
3. OpenAI-compatible API wrapper for container session integration

This adds significant complexity compared to Chainlit's native support.

### Feature Comparison

| Feature | Chainlit | Open WebUI |
|---------|----------|------------|
| Show Tool Execution Steps | ✅ Native `@cl.step` | ⚠️ Custom Pipeline |
| Real-time Streaming | ✅ WebSocket native | ✅ Yes |
| Show Sandbox Logs | ✅ Step input/output | ⚠️ Custom impl |
| Collapsible Details | ✅ Built-in | ❌ Not native |
| Session Per User | ✅ `cl.user_session` | ✅ User management |
| Authentication | ✅ OAuth, Azure AD | ✅ RBAC, LDAP |
| MCP Support | ✅ Native | ⚠️ Via mcpo |
| RAG Built-in | ❌ External lib | ✅ Native |
| Deployment | Low (embed) | Medium (Docker) |

---

## Consequences

### Positive

1. **Faster development** - Native `@cl.step` eliminates need to build custom tool visualization
2. **Single deployment** - Chainlit embeds in our App Service, no separate frontend
3. **Python-only codebase** - Team can focus on Python without frontend skills
4. **Real-time sandbox visibility** - Users see command execution as it happens
5. **Session management built-in** - `cl.user_session` handles per-user state

### Negative

1. **Community maintenance risk** - Original team no longer active
2. **Vendor lock-in** - Some Chainlit-specific patterns in code
3. **Feature uncertainty** - Future feature development depends on community
4. **Potential migration** - May need to migrate if community support declines

### Neutral

1. **Learning curve** - Team needs to learn Chainlit-specific decorators and patterns
2. **Documentation quality** - Adequate but not as extensive as Gradio

---

## Risk Mitigation

### 1. Abstract the UI Layer

Create a clean interface between business logic and Chainlit to enable future migration:

```python
# Abstract interface
class ChatUIInterface(ABC):
    @abstractmethod
    async def show_tool_execution(self, name: str, input: str, output: str): pass

    @abstractmethod
    async def stream_message(self, token: str): pass

# Chainlit implementation
class ChainlitUI(ChatUIInterface):
    async def show_tool_execution(self, name: str, input: str, output: str):
        async with cl.Step(name=name, type="tool") as step:
            step.input = input
            step.output = output
```

### 2. Monitor Community Health

- Watch Chainlit GitHub for maintainer activity
- Track issue response times
- Monitor release frequency
- Participate in community discussions

### 3. Identify Fallback Options

- **Gradio** - Quickest fallback, basic tool UI
- **Open WebUI** - Full-featured fallback, requires architecture change
- **Custom React** - Ultimate fallback, highest development cost

### 4. Contribute to Community

Consider contributing bug fixes and features back to the Chainlit community to help ensure its longevity.

---

## Sources

### Primary Sources

- [Chainlit GitHub Repository](https://github.com/Chainlit/chainlit) - 11.3k stars
- [Chainlit Documentation](https://docs.chainlit.io/)
- [Chainlit Step Documentation](https://docs.chainlit.io/concepts/step)
- [Chainlit Community Maintenance Discussion](https://github.com/Chainlit/chainlit/issues/1115)

### Alternative Frameworks

- [Gradio GitHub](https://github.com/gradio-app/gradio) - 41.1k stars
- [Open WebUI GitHub](https://github.com/open-webui/open-webui) - 119k stars
- [LobeChat GitHub](https://github.com/lobehub/lobe-chat) - 69.6k stars
- [Panel Documentation](https://panel.holoviz.org/reference/chat/ChatInterface.html)
- [Mesop GitHub](https://github.com/mesop-dev/mesop) - 6.3k stars
- [NiceGUI Documentation](https://nicegui.io/documentation/chat_message)

### Comparison Articles

- [Streamlit vs Gradio vs Chainlit: Best UI Framework for LLMs in 2025](https://markaicode.com/streamlit-vs-gradio-vs-chainlit-llm-ui-framework/)
- [LibreChat vs Open WebUI Comparison](https://portkey.ai/blog/librechat-vs-openwebui/)
- [Top 10 Open-Source LLM Interfaces](https://medium.com/@techlatest.net/top-10-open-source-user-interfaces-for-llms-94e3dd4ae20b)
- [Open WebUI Plugin Documentation](https://docs.openwebui.com/features/plugin/)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-30 | sdandey | Initial ADR documenting Chainlit selection with comprehensive comparison of 7 frameworks |
