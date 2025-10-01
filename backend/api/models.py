"""Pydantic models for API requests and responses."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# Research Agent Models


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    user_id: str = Field(..., description="User identifier")
    message: str = Field(..., description="User's message")
    session_id: Optional[str] = Field(None, description="Optional session identifier")


class SessionInfo(BaseModel):
    """Session information."""

    session_id: str
    user_id: str
    created_at: str
    message_count: int


# Crawler Agent Models


class CrawlRequest(BaseModel):
    """Request model for starting a crawl."""

    url: str = Field(..., description="Starting URL")
    intent: str = Field(..., description="Crawl intent/purpose")
    max_depth: Optional[int] = Field(None, description="Override max depth")
    max_pages: Optional[int] = Field(None, description="Override max pages")


class SteerDecision(BaseModel):
    """User steering decision."""

    approve: bool = Field(..., description="Whether to approve the link")
    link: str = Field(..., description="Link being decided on")


class CrawlJobInfo(BaseModel):
    """Crawl job information."""

    job_id: str
    url: str
    intent: str
    status: str  # pending, running, completed, failed
    created_at: str
    pages_crawled: int = 0
    chunks_stored: int = 0


# Knowledge Models


class KnowledgeSearchRequest(BaseModel):
    """Request model for knowledge search."""

    query: str = Field(..., description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")
    domain: Optional[str] = Field(None, description="Filter by domain")


class KnowledgeEntry(BaseModel):
    """Knowledge entry response."""

    id: str
    content: str
    url: str
    title: str
    domain: str
    chunk_index: int
    total_chunks: int
    crawl_date: str
    score: Optional[float] = None


class KnowledgeDeleteRequest(BaseModel):
    """Request model for deleting knowledge."""

    url: str = Field(..., description="URL to delete (supports wildcards)")


# Memory Models


class MemoryStoreRequest(BaseModel):
    """Request model for storing memory."""

    user_id: str = Field(..., description="User identifier")
    content: str = Field(..., description="Memory content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class MemoryLookupRequest(BaseModel):
    """Request model for memory lookup."""

    user_id: str = Field(..., description="User identifier")
    query: str = Field(..., description="Search query")
    limit: int = Field(5, ge=1, le=50, description="Maximum results")


class MemoryEntry(BaseModel):
    """Memory entry response."""

    id: str
    content: str
    metadata: Dict[str, Any]
    score: Optional[float] = None


# Config Models


class ConfigUpdateRequest(BaseModel):
    """Request model for config updates."""

    section: str = Field(..., description="Config section to update")
    updates: Dict[str, Any] = Field(..., description="Values to update")


# Generic Response Models


class SuccessResponse(BaseModel):
    """Generic success response."""

    status: str = "success"
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Generic error response."""

    status: str = "error"
    error: str
    details: Optional[str] = None
