# System Architecture

## Overview

Dual-agent system with shared MCP tools for memory and knowledge management.

```
┌─────────────────────────────────────┐
│         Next.js Frontend            │
│  - Research Chat                    │
│  - Crawler Control                  │
│  - Knowledge Explorer               │
│  - Settings                         │
└─────────────┬───────────────────────┘
              │
    ┌─────────▼─────────┐
    │   FastAPI Backend │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │                   │
┌───▼────┐      ┌──────▼─────┐
│Research│      │  Crawler   │
│ Agent  │      │   Agent    │
│(Claude)│      │  (Ollama)  │
└───┬────┘      └──────┬─────┘
    │                  │
    │    ┌─────────────▼────┐
    └────►   MCP Server     │
         │  - memory tools  │
         │  - knowledge tools│
         └─────────┬─────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
    ┌────▼─────┐      ┌─────▼────┐
    │ ChromaDB │      │ ChromaDB │
    │ memories │      │knowledge │
    │(per-user)│      │ (global) │
    └──────────┘      └──────────┘
```

## Components

### 1. Research Agent
- **Purpose**: Answer user queries using Claude
- **Model**: Anthropic Claude (claude-3-5-sonnet)
- **Features**:
  - Streaming responses via SSE
  - Can lookup user memories
  - Can search knowledge base
  - Tool use visualization

### 2. Crawler Agent
- **Purpose**: Intelligently crawl documentation sites
- **Model**: Ollama (llama3.1)
- **Features**:
  - Respects robots.txt
  - LLM-guided link filtering
  - User steering (approve/reject links)
  - Stores content in knowledge base
  - Real-time progress updates via SSE

### 3. MCP Server
- **Framework**: FastMCP
- **Tools Exposed**:
  - `memory_store` - Store user memory
  - `memory_lookup` - Search user memories
  - `knowledge_store` - Store crawled content
  - `knowledge_search` - Search knowledge base with reranking
  - `knowledge_delete` - Delete by URL

### 4. ChromaDB Storage
- **memories_{user_id}** - Per-user memory collections
- **knowledge_global** - Shared knowledge base
- **Embeddings**: Ollama (nomic-embed-text)

### 5. Frontend
- **Framework**: Next.js 15
- **UI**: shadcn/ui + Tailwind CSS
- **State**: Zustand + TanStack Query
- **Real-time**: SSE (EventSource)

## Data Flow

### Research Query Flow
1. User sends message
2. Frontend → POST /api/research/chat (SSE)
3. Research Agent → Claude API (streaming)
4. Claude may call memory_lookup or knowledge_search
5. MCP Server executes tools
6. Claude generates response with context
7. Stream chunks to frontend via SSE

### Crawl Job Flow
1. User submits URL + intent
2. Frontend → POST /api/crawler/start
3. Crawler Agent:
   - Fetches robots.txt
   - Discovers links
   - Ollama filters by intent
   - Emits SSE events for uncertain links
   - User approves/rejects
   - Crawls approved pages
   - Generates embeddings (Ollama)
   - Stores via knowledge_store
   - Emits progress events
4. Frontend updates in real-time

### Config Update Flow
1. User edits config in Settings
2. Frontend → PUT /api/config
3. Backend validates with Pydantic
4. Updates config.yaml
5. Returns updated config
6. Frontend refreshes

## Technical Decisions

### Why FastMCP?
- Simple Python decorator-based tool definition
- Auto-generates MCP protocol handling
- Easy to extend with new tools

### Why ChromaDB Dual Collections?
- Isolation: User memories are private (per-user collections)
- Sharing: Knowledge base is global
- Simple querying with metadata filters

### Why SSE over WebSockets?
- Simpler for one-way streaming
- Auto-reconnection in browsers
- No need for bidirectional communication
- Works with HTTP/2

### Why Separate Agents?
- Research: Needs best quality (Claude)
- Crawler: Needs local/cheap inference (Ollama)
- Different use cases, different models

## Configuration

Single `config.yaml` with sections:
- `anthropic` - API key, model, tokens
- `ollama` - Base URL, models
- `crawler` - Depth, pages, delays
- `vectordb` - Chunk size, overlap
- `api` - Host, port, CORS

Runtime updates via `/api/config` endpoint.

## SSE Event Types

### Research Agent
- `text` - Text chunk
- `tool_use` - Tool invocation details
- `tool_result` - Tool execution result
- `done` - Completion

### Crawler Agent
- `discovered` - Links found
- `crawling` - Current URL
- `steering_needed` - User approval needed
- `stored` - Content added to KB
- `completed` - Crawl finished
