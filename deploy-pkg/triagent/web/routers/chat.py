"""Chat streaming router for Triagent Web API."""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse

from triagent.web.models import ChatRequest
from triagent.web.services.session_proxy import SessionProxy
from triagent.web.services.session_store import SessionStore

router = APIRouter(tags=["chat"])


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    x_session_id: str = Header(..., alias="X-Session-ID"),
) -> StreamingResponse:
    """Send message and receive streaming SSE response.

    Args:
        request: Chat request with message.
        x_session_id: Session ID from header.

    Returns:
        StreamingResponse with SSE events.
    """
    store = SessionStore()
    proxy = SessionProxy()

    # Look up session and update last active timestamp
    session_data = await store.get_session_by_id(x_session_id)
    if session_data:
        await store.update_last_active(session_data["email"])

    async def generate() -> AsyncGenerator[str, None]:
        """Generate SSE events from session proxy."""
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
