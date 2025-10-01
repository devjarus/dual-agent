"""MCP memory tools for per-user memory management."""

import logging
from typing import Dict, Any, List

from mcp.server import Server

from backend.services.chroma_service import get_chroma_service

logger = logging.getLogger(__name__)


def register_memory_tools(mcp: Server) -> None:
    """Register memory-related MCP tools.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    async def memory_store(
        user_id: str, content: str, metadata: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Store a memory for a specific user.

        Use this tool to save user-specific information, preferences, or context
        that should be remembered across sessions.

        Args:
            user_id: Unique user identifier
            content: Memory content to store
            metadata: Optional metadata (category, source, etc.)

        Returns:
            Dictionary with status and document ID
        """
        try:
            chroma = get_chroma_service()
            doc_id = chroma.store_memory(
                user_id=user_id,
                content=content,
                metadata=metadata or {},
            )

            logger.info(f"Stored memory for user {user_id}")
            return {"status": "success", "id": doc_id}

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return {"status": "error", "error": str(e)}

    @mcp.tool()
    async def memory_lookup(
        user_id: str, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Lookup memories for a specific user using semantic search.

        Use this tool to retrieve relevant user-specific information based on
        a natural language query.

        Args:
            user_id: Unique user identifier
            query: Natural language search query
            limit: Maximum number of results to return (default: 5)

        Returns:
            List of matching memories with content, metadata, and relevance score
        """
        try:
            chroma = get_chroma_service()
            memories = chroma.lookup_memories(
                user_id=user_id,
                query=query,
                limit=limit,
            )

            # Format results for MCP response
            results = []
            for mem in memories:
                results.append(
                    {
                        "id": mem["id"],
                        "content": mem["content"],
                        "score": 1.0 - mem["distance"],  # Convert distance to score
                        "metadata": mem["metadata"],
                    }
                )

            logger.info(f"Found {len(results)} memories for user {user_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to lookup memories: {e}")
            return []
