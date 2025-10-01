# AgentX - AI Research & Crawling Agent System

A dual-agent system combining Claude-powered research with Ollama-powered intelligent web crawling, unified through MCP tools for memory and knowledge management.

## Features

- **Research Agent** - Claude (Anthropic) with streaming responses and tool use
- **Crawler Agent** - Ollama-powered documentation crawler with user steering
- **MCP Server** - Unified memory (per-user) and knowledge (global) tools
- **Modern UI** - Next.js with real-time streaming and config management
- **Developer-Friendly** - One-command setup and start

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Ollama ([install](https://ollama.ai))
- Anthropic API key

### Installation

```bash
# Clone or navigate to project
cd v1-prototype

# One-time setup
make setup

# Update .env with your Anthropic API key
# Edit .env and set ANTHROPIC_API_KEY=your_key_here

# Start all services
make start
```

### Access

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **MCP Server**: http://localhost:8001

## Usage

### Research Agent
1. Navigate to Research page
2. Ask questions
3. See streaming responses with tool use visualization
4. Agent can lookup memories and search knowledge base

### Crawler Agent
1. Navigate to Crawler page
2. Enter URL and intent (e.g., "API documentation only")
3. Watch real-time progress
4. Approve/reject uncertain links
5. View stored knowledge

### Knowledge Explorer
1. Navigate to Knowledge page
2. Search with semantic queries
3. View all crawled content
4. Delete by URL or bulk delete

### Settings
1. Navigate to Settings page
2. Edit configuration (form or JSON mode)
3. Update runtime settings
4. Reset to defaults

## Commands

```bash
make setup    # One-time setup (install deps, pull Ollama models)
make start    # Start all services
make stop     # Stop all services
make dev      # Development mode with tmux
make test     # Run tests
make health   # Check service health
make logs     # Tail all logs
make clean    # Clean build artifacts
```

## Project Structure

```
v1-prototype/
├── docs/                    # Architecture & technical docs
├── backend/                 # Python backend
│   ├── mcp_server/         # MCP server + tools
│   ├── agents/             # Research & Crawler agents
│   ├── api/                # FastAPI routes
│   ├── core/               # Config management
│   └── services/           # Shared services
├── frontend/               # Next.js frontend
├── scripts/                # Development scripts
├── tests/                  # Test suites
└── data/                   # ChromaDB storage
```

## Documentation

- [Architecture](docs/architecture.md) - System design and components
- [Implementation Plan](docs/implementation-plan.md) - Step-by-step build guide
- [Technical Reference](docs/technical-reference.md) - API and tool reference

## Configuration

Edit `backend/config.yaml` or use the Settings UI to configure:

- Anthropic model and parameters
- Ollama models and endpoints
- Crawler settings (depth, pages, delays)
- Vector database settings
- API and MCP server ports

## Development

### Development Mode

```bash
make dev  # Starts services in tmux with auto-reload
```

### Running Tests

```bash
make test
```

### Health Check

```bash
make health
```

## Tech Stack

- **Backend**: FastAPI, FastMCP, ChromaDB, Anthropic SDK, Ollama
- **Frontend**: Next.js 15, React 19, shadcn/ui, Tailwind CSS
- **State**: Zustand, TanStack Query
- **Streaming**: Server-Sent Events (SSE)
- **Storage**: ChromaDB (dual collections)

## Troubleshooting

### Ollama not running
```bash
# Start Ollama
ollama serve

# Verify
curl http://localhost:11434/api/tags
```

### Services won't start
```bash
# Check health
make health

# View logs
make logs

# Clean and restart
make clean
make setup
make start
```

### Missing API key
Update `.env` with your Anthropic API key:
```bash
ANTHROPIC_API_KEY=your_actual_key_here
```

## License

MIT

## Contributing

Contributions welcome! See [DEVELOPMENT.md](DEVELOPMENT.md) for details.
