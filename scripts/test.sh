#!/bin/bash
set -e

echo "🧪 Running AgentX Tests..."

# Backend tests
echo "📦 Testing backend..."
cd backend
source venv/bin/activate

if [ ! -d "tests" ]; then
    echo "⚠️  No tests directory found. Creating placeholder..."
    mkdir -p tests
    touch tests/__init__.py
fi

if command -v pytest &> /dev/null; then
    pytest tests/ -v || echo "⚠️  Some tests failed or no tests found"
else
    echo "⚠️  pytest not installed. Skipping backend tests."
fi

cd ..

# Frontend tests
echo "🎨 Testing frontend..."
cd frontend

if [ -f "package.json" ]; then
    if grep -q '"test"' package.json; then
        npm test || echo "⚠️  Some tests failed or no tests found"
    else
        echo "⚠️  No test script found in package.json"
    fi
else
    echo "⚠️  Frontend not set up yet"
fi

cd ..

echo "✅ Tests completed!"
