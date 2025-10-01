"""Research Agent API routes."""

import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.api.models import ChatRequest, SuccessResponse
from backend.agents.research_agent import ResearchAgent

logger = logging.getLogger(__name__)

router = APIRouter()

# Global agent instance
_research_agent: ResearchAgent | None = None


def get_research_agent() -> ResearchAgent:
    """Get or create research agent instance."""
    global _research_agent
    if _research_agent is None:
        _research_agent = ResearchAgent()
    return _research_agent


@router.post("/chat")
async def research_chat(request: ChatRequest):
    """Stream chat response from Research Agent.

    Returns Server-Sent Events (SSE) stream with:
    - text: Text chunks from Claude
    - tool_use: Tool calls being made
    - tool_result: Results from tool execution
    - done: Conversation complete
    - error: Error occurred

    Example:
        POST /api/research/chat
        {
            "user_id": "user_123",
            "message": "What is RAG?",
            "session_id": "session_456"
        }
    """
    try:
        agent = get_research_agent()

        async def event_stream() -> AsyncGenerator[str, None]:
            """Generate SSE events."""
            try:
                async for event in agent.stream_chat(
                    user_id=request.user_id,
                    message=request.message,
                    session_id=request.session_id,
                ):
                    yield event
            except Exception as e:
                logger.error(f"Error in research chat stream: {e}", exc_info=True)
                # Send error event
                import json

                error_event = {
                    "type": "error",
                    "error": str(e),
                }
                yield f"event: error\ndata: {json.dumps(error_event)}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable buffering in nginx
            },
        )

    except Exception as e:
        logger.error(f"Failed to start research chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{user_id}")
async def list_sessions(user_id: str):
    """List chat sessions for a user.

    TODO: Implement session management and storage.

    Example:
        GET /api/research/sessions/user_123
    """
    # TODO: Implement session storage and retrieval
    return {
        "user_id": user_id,
        "sessions": [],
        "message": "Session management not yet implemented",
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> SuccessResponse:
    """Delete a chat session.

    TODO: Implement session deletion.

    Example:
        DELETE /api/research/sessions/session_456
    """
    # TODO: Implement session deletion
    return SuccessResponse(
        message=f"Session {session_id} deleted (not yet implemented)"
    )
