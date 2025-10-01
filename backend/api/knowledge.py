"""Knowledge base API routes."""

import logging
from typing import List

from fastapi import APIRouter, HTTPException

from backend.api.models import (
    KnowledgeSearchRequest,
    KnowledgeEntry,
    KnowledgeDeleteRequest,
    SuccessResponse,
)
from backend.services.chroma_service import get_chroma_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search")
async def search_knowledge(request: KnowledgeSearchRequest) -> List[KnowledgeEntry]:
    """Search the global knowledge base.

    Example:
        POST /api/knowledge/search
        {
            "query": "what is RAG",
            "limit": 10,
            "domain": "example.com"
        }
    """
    try:
        chroma = get_chroma_service()

        results = chroma.search_knowledge(
            query=request.query,
            limit=request.limit,
            domain=request.domain,
        )

        # Format results
        entries = []
        for result in results:
            entry = KnowledgeEntry(
                id=result["id"],
                content=result["content"],
                url=result["metadata"].get("url", ""),
                title=result["metadata"].get("title", ""),
                domain=result["metadata"].get("domain", ""),
                chunk_index=result["metadata"].get("chunk_index", 0),
                total_chunks=result["metadata"].get("total_chunks", 1),
                crawl_date=result["metadata"].get("crawl_date", ""),
                score=1.0 - result["distance"],  # Convert distance to score
            )
            entries.append(entry)

        logger.info(f"Knowledge search: found {len(entries)} results")
        return entries

    except Exception as e:
        logger.error(f"Failed to search knowledge: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/browse")
async def browse_knowledge(
    limit: int = 50, offset: int = 0
) -> List[KnowledgeEntry]:
    """Browse all knowledge entries.

    Example:
        GET /api/knowledge/browse?limit=50&offset=0
    """
    try:
        chroma = get_chroma_service()

        # Get all knowledge (simplified - no offset support in current implementation)
        results = chroma.get_all_knowledge(limit=limit)

        # Format results
        entries = []
        for result in results:
            entry = KnowledgeEntry(
                id=result["id"],
                content=result["content"],
                url=result["metadata"].get("url", ""),
                title=result["metadata"].get("title", ""),
                domain=result["metadata"].get("domain", ""),
                chunk_index=result["metadata"].get("chunk_index", 0),
                total_chunks=result["metadata"].get("total_chunks", 1),
                crawl_date=result["metadata"].get("crawl_date", ""),
            )
            entries.append(entry)

        logger.info(f"Knowledge browse: returned {len(entries)} entries")
        return entries

    except Exception as e:
        logger.error(f"Failed to browse knowledge: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete")
async def delete_knowledge(request: KnowledgeDeleteRequest) -> SuccessResponse:
    """Delete knowledge by URL or domain.

    Supports wildcards for bulk deletion (e.g., "example.com/*")

    Example:
        DELETE /api/knowledge/delete
        {
            "url": "https://example.com/docs"
        }

        Or for bulk deletion:
        {
            "url": "example.com/*"
        }
    """
    try:
        chroma = get_chroma_service()

        # Check for wildcard pattern
        if request.url.endswith("/*"):
            # Delete by domain
            domain = request.url.rstrip("/*")
            deleted_count = chroma.delete_knowledge_by_domain(domain)
        else:
            # Delete by exact URL
            deleted_count = chroma.delete_knowledge_by_url(request.url)

        logger.info(f"Deleted {deleted_count} knowledge entries for {request.url}")

        return SuccessResponse(
            message=f"Deleted {deleted_count} knowledge entries",
            data={"deleted_count": deleted_count, "url": request.url},
        )

    except Exception as e:
        logger.error(f"Failed to delete knowledge: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def knowledge_stats():
    """Get knowledge base statistics.

    Example:
        GET /api/knowledge/stats
    """
    try:
        chroma = get_chroma_service()

        # Get all knowledge to calculate stats
        all_knowledge = chroma.get_all_knowledge()

        # Calculate stats
        total_chunks = len(all_knowledge)
        unique_urls = set()
        unique_domains = set()

        for entry in all_knowledge:
            url = entry["metadata"].get("url", "")
            domain = entry["metadata"].get("domain", "")
            if url:
                unique_urls.add(url)
            if domain:
                unique_domains.add(domain)

        stats = {
            "total_chunks": total_chunks,
            "unique_urls": len(unique_urls),
            "unique_domains": len(unique_domains),
        }

        logger.info(f"Knowledge stats: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Failed to get knowledge stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
