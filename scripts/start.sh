#!/bin/bash
set -e

echo "🚀 Starting AgentX System..."

# Check if Ollama is running
check_ollama() {
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "❌ Ollama is not running. Please start Ollama first."
        exit 1
    fi
    echo "✅ Ollama is running"
}

# Check environment
check_env() {
    if [ ! -f ".env" ]; then
        echo "⚠️  .env file not found. Copying from .env.example..."
        cp .env.example .env
        echo "⚠️  Please update .env with your API keys"
        exit 1
    fi

    # Source env file
    export $(cat .env | grep -v '^#' | xargs)

    if [ "$ANTHROPIC_API_KEY" = "your_api_key_here" ]; then
        echo "⚠️  Please update ANTHROPIC_API_KEY in .env"
        exit 1
    fi

    echo "✅ Environment file found"
}

# Start backend
start_backend() {
    echo "📦 Starting backend..."
    cd backend

    if [ ! -d "venv" ]; then
        echo "❌ Virtual environment not found. Run: make setup"
        exit 1
    fi

    source venv/bin/activate

    # Start MCP server in background
    echo "🔧 Starting MCP server..."
    python -m mcp_server.server > ../logs/mcp.log 2>&1 &
    echo $! > ../logs/mcp.pid

    # Start API server in background
    echo "🌐 Starting API server..."
    uvicorn api.main:app --host 0.0.0.0 --port 8000 > ../logs/api.log 2>&1 &
    echo $! > ../logs/api.pid

    cd ..
}

# Start frontend
start_frontend() {
    echo "🎨 Starting frontend..."
    cd frontend

    if [ ! -d "node_modules" ]; then
        echo "❌ node_modules not found. Run: make setup"
        exit 1
    fi

    npm run dev > ../logs/frontend.log 2>&1 &
    echo $! > ../logs/frontend.pid
    cd ..
}

# Wait for services
wait_for_services() {
    echo "⏳ Waiting for services to start..."
    sleep 3

    # Check MCP server
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ MCP server is ready"
    else
        echo "⚠️  MCP server starting..."
    fi

    # Check API server
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API server is ready"
    else
        echo "⚠️  API server starting..."
    fi

    # Check frontend
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend is ready"
    else
        echo "⚠️  Frontend is starting (may take a minute)..."
    fi
}

# Main
mkdir -p logs

check_ollama
check_env
start_backend
start_frontend
wait_for_services

echo ""
echo "✨ AgentX is running!"
echo "📊 Frontend: http://localhost:3000"
echo "🔌 API: http://localhost:8000/docs"
echo "🔧 MCP: http://localhost:8001"
echo ""
echo "📝 Logs:"
echo "  - API: logs/api.log"
echo "  - MCP: logs/mcp.log"
echo "  - Frontend: logs/frontend.log"
echo ""
echo "To stop: make stop"
