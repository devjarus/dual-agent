"""MCP knowledge tools for global knowledge base management."""

import logging
from typing import Dict, Any, List
from urllib.parse import urlparse

from mcp.server import Server

from backend.services.chroma_service import get_chroma_service
from backend.core.config import get_settings

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks.

    Args:
        text: Text to chunk
        chunk_size: Target chunk size in characters (approximation for tokens)
        overlap: Overlap between chunks in characters

    Returns:
        List of text chunks
    """
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind(".")
            last_newline = chunk.rfind("\n")
            break_point = max(last_period, last_newline)

            if break_point > chunk_size * 0.5:  # Only break if reasonable position
                chunk = chunk[: break_point + 1]
                end = start + break_point + 1

        chunks.append(chunk.strip())
        start = end - overlap

    return chunks


def register_knowledge_tools(mcp: Server) -> None:
    """Register knowledge-related MCP tools.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    async def knowledge_store(
        content: str, url: str, metadata: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Store content in the global knowledge base.

        Automatically chunks the content and stores it with metadata.
        Use this tool to add documentation, articles, or reference material
        to the shared knowledge base.

        Args:
            content: Content to store
            url: Source URL (used as unique identifier)
            metadata: Optional metadata (title, domain, etc.)

        Returns:
            Dictionary with status and number of chunks created
        """
        try:
            settings = get_settings()
            chroma = get_chroma_service()

            # Extract metadata
            metadata = metadata or {}
            title = metadata.get("title", url)
            parsed_url = urlparse(url)
            domain = metadata.get("domain", parsed_url.netloc)

            # Chunk content
            chunks = chunk_text(
                content,
                chunk_size=settings.vectordb.chunk_size,
                overlap=settings.vectordb.chunk_overlap,
            )

            if not chunks:
                return {"status": "error", "error": "No content to store"}

            # Store each chunk
            for i, chunk in enumerate(chunks):
                chroma.store_knowledge(
                    content=chunk,
                    url=url,
                    title=title,
                    chunk_index=i,
                    total_chunks=len(chunks),
                    domain=domain,
                )

            logger.info(f"Stored {len(chunks)} chunks from {url}")
            return {"status": "success", "chunks": len(chunks)}

        except Exception as e:
            logger.error(f"Failed to store knowledge: {e}")
            return {"status": "error", "error": str(e)}

    @mcp.tool()
    async def knowledge_search(
        query: str, limit: int = 5, rerank: bool = False
    ) -> List[Dict[str, Any]]:
        """Search the global knowledge base.

        Performs semantic search across all stored knowledge. Optionally
        reranks results using Ollama for improved relevance.

        Args:
            query: Natural language search query
            limit: Maximum number of results (default: 5)
            rerank: Whether to rerank results with Ollama (default: False)

        Returns:
            List of matching knowledge chunks with content, metadata, and scores
        """
        try:
            chroma = get_chroma_service()
            results = chroma.search_knowledge(query=query, limit=limit)

            # Format results for MCP response
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "id": result["id"],
                        "content": result["content"],
                        "score": 1.0 - result["distance"],  # Convert distance to score
                        "url": result["metadata"].get("url"),
                        "metadata": result["metadata"],
                    }
                )

            # TODO: Implement reranking with Ollama if requested
            if rerank and formatted_results:
                logger.debug("Reranking requested but not yet implemented")
                # Future: Use Ollama reranking model

            logger.info(f"Found {len(formatted_results)} knowledge results")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search knowledge: {e}")
            return []

    @mcp.tool()
    async def knowledge_delete(url: str) -> Dict[str, Any]:
        """Delete all knowledge entries from a specific URL.

        Use this tool to remove outdated or incorrect information from
        the knowledge base. Supports wildcard patterns for bulk deletion.

        Args:
            url: Source URL to delete (supports wildcards: domain/*)

        Returns:
            Dictionary with status and number of deleted entries
        """
        try:
            chroma = get_chroma_service()

            # Check for wildcard pattern (domain/*)
            if url.endswith("/*"):
                # Extract domain and delete by domain
                domain = url.rstrip("/*")
                deleted_count = chroma.delete_knowledge_by_domain(domain)
            else:
                # Delete by exact URL
                deleted_count = chroma.delete_knowledge_by_url(url)

            logger.info(f"Deleted {deleted_count} knowledge entries for {url}")
            return {"status": "success", "deleted": deleted_count}

        except Exception as e:
            logger.error(f"Failed to delete knowledge: {e}")
            return {"status": "error", "error": str(e)}
