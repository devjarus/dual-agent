"""FastAPI application main entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.api import research, crawler, knowledge, memory, config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/api.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting AgentX API server...")

    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    # Load settings
    settings = get_settings()
    logger.info(f"Loaded configuration from config.yaml")

    yield

    # Shutdown
    logger.info("Shutting down AgentX API server...")


# Create FastAPI app
app = FastAPI(
    title="AgentX API",
    description="Dual-agent system with Research and Crawler agents",
    version="0.1.0",
    lifespan=lifespan,
)

# Get settings for CORS
settings = get_settings()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(research.router, prefix="/api/research", tags=["Research Agent"])
app.include_router(crawler.router, prefix="/api/crawler", tags=["Crawler Agent"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
app.include_router(config.router, prefix="/api/config", tags=["Configuration"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AgentX API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "mcp_server": "unknown",  # TODO: Check MCP server health
            "ollama": "unknown",  # TODO: Check Ollama health
        },
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=True,
        log_level=settings.api.log_level,
    )
