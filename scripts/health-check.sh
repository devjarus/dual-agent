#!/bin/bash

check_service() {
    local name=$1
    local url=$2

    if curl -sf "$url" > /dev/null 2>&1; then
        echo "✅ $name is healthy"
        return 0
    else
        echo "❌ $name is not responding"
        return 1
    fi
}

echo "🏥 Health Check..."
echo ""

all_healthy=0

check_service "Ollama" "http://localhost:11434/api/tags" || all_healthy=1
check_service "MCP Server" "http://localhost:8001/health" || all_healthy=1
check_service "API Server" "http://localhost:8000/health" || all_healthy=1
check_service "Frontend" "http://localhost:3000" || all_healthy=1

echo ""
if [ $all_healthy -eq 0 ]; then
    echo "✅ All services healthy"
else
    echo "⚠️  Some services are down"
fi

exit $all_healthy
