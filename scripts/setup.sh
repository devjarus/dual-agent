#!/bin/bash
set -e

echo "⚙️  Setting up AgentX..."

# Check prerequisites
check_prereqs() {
    echo "Checking prerequisites..."

    command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.11+ required"; exit 1; }
    command -v node >/dev/null 2>&1 || { echo "❌ Node.js 18+ required"; exit 1; }
    command -v ollama >/dev/null 2>&1 || { echo "❌ Ollama required. Install from https://ollama.ai"; exit 1; }

    echo "✅ Prerequisites satisfied"
}

# Setup backend
setup_backend() {
    echo "📦 Setting up backend..."
    cd backend

    # Create venv
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate

    # Install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt

    cd ..
}

# Setup frontend
setup_frontend() {
    echo "🎨 Setting up frontend..."

    if [ ! -d "frontend/package.json" ]; then
        echo "Creating Next.js app..."
        cd frontend
        npx create-next-app@latest . --typescript --tailwind --app --no-git --import-alias "@/*"
        cd ..
    else
        echo "Frontend already initialized"
        cd frontend
        npm install
        cd ..
    fi
}

# Pull Ollama models
setup_ollama() {
    echo "🤖 Pulling Ollama models..."

    if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "⚠️  Ollama is not running. Please start Ollama first."
        echo "   After starting Ollama, run: ollama pull nomic-embed-text && ollama pull llama3.1"
        return
    fi

    ollama pull nomic-embed-text
    ollama pull llama3.1
}

# Create env file
setup_env() {
    if [ ! -f .env ]; then
        echo "📝 Creating .env file..."
        cp .env.example .env
        echo "⚠️  Please update .env with your ANTHROPIC_API_KEY"
    else
        echo "✅ .env file exists"
    fi
}

# Create data directories
setup_directories() {
    echo "📁 Creating data directories..."
    mkdir -p data/chroma
    mkdir -p logs
}

# Main
check_prereqs
setup_directories
setup_backend
setup_frontend
setup_ollama
setup_env

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your Anthropic API key"
echo "2. Ensure Ollama is running"
echo "3. Run: make start"
