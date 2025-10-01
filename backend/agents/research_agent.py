"""Research Agent using Claude (Anthropic) with MCP tools."""

import json
import logging
from typing import AsyncGenerator, Dict, Any, List

from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import (
    Message,
    MessageStreamEvent,
    ContentBlockDeltaEvent,
    TextDelta,
)

from backend.core.config import get_settings
from backend.services.chroma_service import get_chroma_service

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Research agent powered by Claude with memory and knowledge tools."""

    def __init__(self):
        """Initialize Research Agent with Anthropic client and MCP tools."""
        settings = get_settings()

        # Initialize Anthropic client
        self.client = AsyncAnthropic(api_key=settings.anthropic.api_key)
        self.model = settings.anthropic.model
        self.max_tokens = settings.anthropic.max_tokens
        self.temperature = settings.anthropic.temperature

        # ChromaDB service for tool calls
        self.chroma = get_chroma_service()

        # Define MCP tools in Anthropic format
        self.tools = [
            {
                "name": "memory_lookup",
                "description": "Lookup user memories using semantic search. Use this to recall user preferences, past conversations, or context.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 5)",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "memory_store",
                "description": "Store important information about the user for future reference. Use this to remember preferences, facts, or context.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Information to remember",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Optional metadata (category, source)",
                            "properties": {
                                "category": {"type": "string"},
                                "source": {"type": "string"},
                            },
                        },
                    },
                    "required": ["content"],
                },
            },
            {
                "name": "knowledge_search",
                "description": "Search the global knowledge base for information. Use this to find documentation, articles, or reference material.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 5)",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
        ]

        logger.info("Research Agent initialized")

    async def _call_tool(
        self, tool_name: str, tool_input: Dict[str, Any], user_id: str
    ) -> Any:
        """Execute MCP tool call.

        Args:
            tool_name: Name of the tool to call
            tool_input: Input parameters for the tool
            user_id: User identifier for memory operations

        Returns:
            Tool execution result
        """
        try:
            if tool_name == "memory_lookup":
                results = self.chroma.lookup_memories(
                    user_id=user_id,
                    query=tool_input["query"],
                    limit=tool_input.get("limit", 5),
                )
                # Format for Claude
                return [
                    {
                        "content": r["content"],
                        "score": 1.0 - r["distance"],
                        "metadata": r["metadata"],
                    }
                    for r in results
                ]

            elif tool_name == "memory_store":
                doc_id = self.chroma.store_memory(
                    user_id=user_id,
                    content=tool_input["content"],
                    metadata=tool_input.get("metadata", {}),
                )
                return {"status": "success", "id": doc_id}

            elif tool_name == "knowledge_search":
                results = self.chroma.search_knowledge(
                    query=tool_input["query"],
                    limit=tool_input.get("limit", 5),
                )
                # Format for Claude
                return [
                    {
                        "content": r["content"],
                        "url": r["metadata"].get("url"),
                        "title": r["metadata"].get("title"),
                        "score": 1.0 - r["distance"],
                    }
                    for r in results
                ]

            else:
                raise ValueError(f"Unknown tool: {tool_name}")

        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}")
            return {"error": str(e)}

    async def stream_chat(
        self,
        user_id: str,
        message: str,
        session_id: str | None = None,
        conversation_history: List[Dict[str, Any]] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat response with tool use.

        Args:
            user_id: User identifier
            message: User's message
            session_id: Optional session identifier
            conversation_history: Optional conversation history

        Yields:
            SSE-formatted events (text, tool_use, tool_result, done)
        """
        try:
            # Build messages
            messages = conversation_history or []
            messages.append({"role": "user", "content": message})

            logger.info(f"Research agent streaming response for user {user_id}")

            # Stream response from Claude
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=messages,
                tools=self.tools,
            ) as stream:
                # Track tool calls for this turn
                current_tool_use = None

                async for event in stream:
                    # Text delta
                    if isinstance(event, ContentBlockDeltaEvent):
                        if isinstance(event.delta, TextDelta):
                            # Emit text chunk
                            yield self._format_sse(
                                "text",
                                {"chunk": event.delta.text},
                            )

                    # Tool use started
                    elif hasattr(event, "type") and event.type == "content_block_start":
                        if hasattr(event, "content_block") and hasattr(
                            event.content_block, "type"
                        ):
                            if event.content_block.type == "tool_use":
                                current_tool_use = {
                                    "id": event.content_block.id,
                                    "name": event.content_block.name,
                                    "input": {},
                                }

                    # Tool input delta
                    elif (
                        hasattr(event, "type") and event.type == "content_block_delta"
                    ):
                        if (
                            current_tool_use
                            and hasattr(event, "delta")
                            and hasattr(event.delta, "type")
                        ):
                            if event.delta.type == "input_json_delta":
                                # Accumulate tool input
                                pass  # Input will be complete in tool_use event

                    # Tool use complete
                    elif hasattr(event, "type") and event.type == "content_block_stop":
                        if current_tool_use:
                            # Get final message to extract tool input
                            final_message = await stream.get_final_message()

                            for block in final_message.content:
                                if (
                                    hasattr(block, "type")
                                    and block.type == "tool_use"
                                ):
                                    if block.id == current_tool_use["id"]:
                                        # Emit tool_use event
                                        yield self._format_sse(
                                            "tool_use",
                                            {
                                                "tool": block.name,
                                                "args": block.input,
                                            },
                                        )

                                        # Execute tool
                                        result = await self._call_tool(
                                            block.name, block.input, user_id
                                        )

                                        # Emit tool_result event
                                        yield self._format_sse(
                                            "tool_result",
                                            {"result": result},
                                        )

                                        # Continue conversation with tool result
                                        messages.append(
                                            {
                                                "role": "assistant",
                                                "content": final_message.content,
                                            }
                                        )
                                        messages.append(
                                            {
                                                "role": "user",
                                                "content": [
                                                    {
                                                        "type": "tool_result",
                                                        "tool_use_id": block.id,
                                                        "content": json.dumps(result),
                                                    }
                                                ],
                                            }
                                        )

                                        # Continue streaming
                                        async for continuation_event in self.stream_chat(
                                            user_id=user_id,
                                            message="",  # Empty message for continuation
                                            session_id=session_id,
                                            conversation_history=messages,
                                        ):
                                            yield continuation_event

                                        return

                            current_tool_use = None

            # Emit done event
            yield self._format_sse("done", {"session_id": session_id or "default"})

        except Exception as e:
            logger.error(f"Research agent error: {e}", exc_info=True)
            yield self._format_sse("error", {"error": str(e)})

    def _format_sse(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format data as Server-Sent Event.

        Args:
            event_type: Event type (text, tool_use, tool_result, done, error)
            data: Event data

        Returns:
            SSE-formatted string
        """
        event_data = {"type": event_type, **data}
        return f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"
