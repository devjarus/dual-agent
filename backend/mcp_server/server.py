"""MCP Server main entry point."""

import logging
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from mcp.server import Server
from mcp.server.stdio import stdio_server

from backend.core.config import get_settings
from backend.mcp_server.memory_tools import register_memory_tools
from backend.mcp_server.knowledge_tools import register_knowledge_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/mcp_server.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def create_mcp_server() -> Server:
    """Create and configure MCP server with all tools.

    Returns:
        Configured MCP server instance
    """
    # Load settings
    settings = get_settings()

    # Create MCP server
    mcp = Server("agentx-mcp")

    # Register all tools
    logger.info("Registering MCP tools...")
    register_memory_tools(mcp)
    register_knowledge_tools(mcp)

    logger.info("MCP server configured successfully")
    return mcp


async def main():
    """Run the MCP server."""
    try:
        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)

        logger.info("Starting AgentX MCP Server...")

        # Create server
        mcp = create_mcp_server()

        # Run server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP server running on stdio")
            await mcp.run(
                read_stream,
                write_stream,
                mcp.create_initialization_options(),
            )

    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"MCP server error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
