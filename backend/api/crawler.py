"""Crawler Agent API routes."""

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict
from uuid import uuid4

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from backend.api.models import (
    CrawlRequest,
    SteerDecision,
    CrawlJobInfo,
    SuccessResponse,
)
from backend.agents.crawler_agent import CrawlerAgent

logger = logging.getLogger(__name__)

router = APIRouter()

# Global agent instance
_crawler_agent: CrawlerAgent | None = None

# Active crawl jobs
_active_jobs: Dict[str, Dict] = {}

# Steering queues for each job
_steering_queues: Dict[str, asyncio.Queue] = {}


def get_crawler_agent() -> CrawlerAgent:
    """Get or create crawler agent instance."""
    global _crawler_agent
    if _crawler_agent is None:
        _crawler_agent = CrawlerAgent()
    return _crawler_agent


@router.post("/start")
async def start_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """Start a new crawl job.

    Returns job information with job_id for streaming and steering.

    Example:
        POST /api/crawler/start
        {
            "url": "https://example.com",
            "intent": "API documentation only",
            "max_depth": 3,
            "max_pages": 50
        }

        Response:
        {
            "job_id": "abc123",
            "url": "https://example.com",
            "status": "pending",
            "stream_url": "/api/crawler/jobs/abc123/stream",
            "steer_url": "/api/crawler/jobs/abc123/steer"
        }
    """
    try:
        # Generate job ID
        job_id = str(uuid4())

        # Create steering queue
        _steering_queues[job_id] = asyncio.Queue()

        # Store job info
        _active_jobs[job_id] = {
            "job_id": job_id,
            "url": request.url,
            "intent": request.intent,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "pages_crawled": 0,
            "chunks_stored": 0,
        }

        logger.info(f"Created crawl job {job_id} for {request.url}")

        return {
            "job_id": job_id,
            "url": request.url,
            "intent": request.intent,
            "status": "pending",
            "stream_url": f"/api/crawler/jobs/{job_id}/stream",
            "steer_url": f"/api/crawler/jobs/{job_id}/steer",
        }

    except Exception as e:
        logger.error(f"Failed to start crawl: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/stream")
async def crawl_stream(job_id: str):
    """Stream crawl progress and events.

    Returns Server-Sent Events (SSE) stream with:
    - discovered: New links discovered
    - crawling: Currently crawling URL
    - steering_needed: User input needed for link
    - stored: Content stored in knowledge base
    - completed: Crawl finished
    - error: Error occurred

    Example:
        GET /api/crawler/jobs/abc123/stream
    """
    try:
        if job_id not in _active_jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        agent = get_crawler_agent()
        job_info = _active_jobs[job_id]

        # Update status
        _active_jobs[job_id]["status"] = "running"

        async def event_stream() -> AsyncGenerator[str, None]:
            """Generate SSE events."""
            try:
                # Get steering queue for this job
                steering_queue = _steering_queues.get(job_id)

                async for event in agent.crawl_with_steering(
                    start_url=job_info["url"],
                    intent=job_info["intent"],
                    steering_queue=steering_queue,
                ):
                    yield event

                # Mark job as completed
                _active_jobs[job_id]["status"] = "completed"

            except Exception as e:
                logger.error(f"Error in crawl stream: {e}", exc_info=True)
                _active_jobs[job_id]["status"] = "failed"

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
                "X-Accel-Buffering": "no",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start crawl stream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/steer")
async def steer_crawl(job_id: str, decision: SteerDecision) -> SuccessResponse:
    """Provide steering decision for a link.

    Example:
        POST /api/crawler/jobs/abc123/steer
        {
            "approve": true,
            "link": "https://example.com/docs"
        }
    """
    try:
        if job_id not in _active_jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        if job_id not in _steering_queues:
            raise HTTPException(status_code=400, detail="No steering queue for job")

        # Put decision in queue
        await _steering_queues[job_id].put(decision.dict())

        logger.info(
            f"Steering decision for job {job_id}: "
            f"{'approve' if decision.approve else 'reject'} {decision.link}"
        )

        return SuccessResponse(
            message=f"Steering decision recorded: "
            f"{'approved' if decision.approve else 'rejected'}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process steering decision: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_job_info(job_id: str) -> CrawlJobInfo:
    """Get information about a crawl job.

    Example:
        GET /api/crawler/jobs/abc123
    """
    if job_id not in _active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return CrawlJobInfo(**_active_jobs[job_id])


@router.get("/jobs")
async def list_jobs():
    """List all crawl jobs.

    Example:
        GET /api/crawler/jobs
    """
    return {
        "jobs": [CrawlJobInfo(**job_info) for job_info in _active_jobs.values()],
        "total": len(_active_jobs),
    }


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str) -> SuccessResponse:
    """Delete a crawl job.

    Example:
        DELETE /api/crawler/jobs/abc123
    """
    if job_id not in _active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    # Remove from active jobs
    del _active_jobs[job_id]

    # Clean up steering queue
    if job_id in _steering_queues:
        del _steering_queues[job_id]

    logger.info(f"Deleted crawl job {job_id}")

    return SuccessResponse(message=f"Job {job_id} deleted")
