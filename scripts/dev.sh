#!/bin/bash
# Development mode with auto-reload and verbose logging

export LOG_LEVEL=debug

echo "🔧 Starting AgentX in development mode..."

# Check if tmux is available
if command -v tmux &> /dev/null; then
    echo "Using tmux for better development experience..."

    # Kill existing session if it exists
    tmux kill-session -t agentx 2>/dev/null

    # Create new session
    tmux new-session -d -s agentx -n backend

    # Window 0: Backend services split
    tmux send-keys -t agentx:backend 'cd backend && source venv/bin/activate && echo "Starting MCP Server..." && python -m mcp_server.server' C-m
    tmux split-window -t agentx:backend -h
    tmux send-keys -t agentx:backend.1 'cd backend && source venv/bin/activate && sleep 2 && echo "Starting API Server..." && uvicorn api.main:app --reload --log-level debug' C-m

    # Window 1: Frontend
    tmux new-window -t agentx -n frontend
    tmux send-keys -t agentx:frontend 'cd frontend && npm run dev' C-m

    # Window 2: Logs
    tmux new-window -t agentx -n logs
    tmux send-keys -t agentx:logs 'sleep 5 && tail -f logs/*.log' C-m

    # Attach to session
    tmux attach -t agentx
else
    echo "tmux not found. Install tmux for better dev experience: brew install tmux"
    echo "Falling back to regular start..."
    ./scripts/start.sh
fi
