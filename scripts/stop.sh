#!/bin/bash

echo "🛑 Stopping AgentX System..."

# Kill processes
if [ -f logs/mcp.pid ]; then
    kill $(cat logs/mcp.pid) 2>/dev/null && echo "✅ MCP server stopped"
    rm logs/mcp.pid
fi

if [ -f logs/api.pid ]; then
    kill $(cat logs/api.pid) 2>/dev/null && echo "✅ API server stopped"
    rm logs/api.pid
fi

if [ -f logs/frontend.pid ]; then
    kill $(cat logs/frontend.pid) 2>/dev/null && echo "✅ Frontend stopped"
    rm logs/frontend.pid
fi

# Cleanup any remaining processes
pkill -f "uvicorn api.main:app" 2>/dev/null
pkill -f "mcp_server.server" 2>/dev/null
pkill -f "next dev" 2>/dev/null

echo "✨ All services stopped"
