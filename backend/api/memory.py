"""Memory API routes for per-user memory management."""

import logging
from typing import List

from fastapi import APIRouter, HTTPException

from backend.api.models import (
    MemoryStoreRequest,
    MemoryLookupRequest,
    MemoryEntry,
    SuccessResponse,
)
from backend.services.chroma_service import get_chroma_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/store")
async def store_memory(request: MemoryStoreRequest) -> SuccessResponse:
    """Store a memory for a specific user.

    Example:
        POST /api/memory/store
        {
            "user_id": "user_123",
            "content": "User prefers dark mode",
            "metadata": {
                "category": "preference",
                "source": "chat"
            }
        }
    """
    try:
        chroma = get_chroma_service()

        doc_id = chroma.store_memory(
            user_id=request.user_id,
            content=request.content,
            metadata=request.metadata or {},
        )

        logger.info(f"Stored memory for user {request.user_id}: {doc_id}")

        return SuccessResponse(
            message="Memory stored successfully",
            data={"id": doc_id, "user_id": request.user_id},
        )

    except Exception as e:
        logger.error(f"Failed to store memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lookup")
async def lookup_memories(request: MemoryLookupRequest) -> List[MemoryEntry]:
    """Lookup memories for a user using semantic search.

    Example:
        POST /api/memory/lookup
        {
            "user_id": "user_123",
            "query": "user preferences",
            "limit": 5
        }
    """
    try:
        chroma = get_chroma_service()

        results = chroma.lookup_memories(
            user_id=request.user_id,
            query=request.query,
            limit=request.limit,
        )

        # Format results
        entries = []
        for result in results:
            entry = MemoryEntry(
                id=result["id"],
                content=result["content"],
                metadata=result["metadata"],
                score=1.0 - result["distance"],  # Convert distance to score
            )
            entries.append(entry)

        logger.info(f"Memory lookup for user {request.user_id}: found {len(entries)} results")
        return entries

    except Exception as e:
        logger.error(f"Failed to lookup memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
async def get_user_memories(user_id: str, limit: int = 50) -> List[MemoryEntry]:
    """Get all memories for a specific user.

    Example:
        GET /api/memory/user/user_123?limit=50
    """
    try:
        chroma = get_chroma_service()

        # Use a broad query to get all memories
        results = chroma.lookup_memories(
            user_id=user_id,
            query="",  # Empty query to get all
            limit=limit,
        )

        # Format results
        entries = []
        for result in results:
            entry = MemoryEntry(
                id=result["id"],
                content=result["content"],
                metadata=result["metadata"],
                score=1.0 - result["distance"],
            )
            entries.append(entry)

        logger.info(f"Retrieved {len(entries)} memories for user {user_id}")
        return entries

    except Exception as e:
        logger.error(f"Failed to get user memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/user/{user_id}")
async def delete_user_memories(user_id: str) -> SuccessResponse:
    """Delete all memories for a specific user.

    Example:
        DELETE /api/memory/user/user_123
    """
    try:
        chroma = get_chroma_service()

        chroma.reset_memory_collection(user_id)

        logger.info(f"Deleted all memories for user {user_id}")

        return SuccessResponse(
            message=f"All memories deleted for user {user_id}",
            data={"user_id": user_id},
        )

    except Exception as e:
        logger.error(f"Failed to delete user memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
