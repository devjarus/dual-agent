# Implementation Plan

## Prerequisites

- Python 3.11+
- Node.js 18+
- Ollama installed and running
- Anthropic API key

## Phase 1: Foundation

### 1.1 Project Structure
```bash
mkdir -p backend/{mcp_server,agents,api,core,services}
mkdir -p frontend/src/{app,components,hooks,stores}
mkdir -p scripts tests data logs
```

### 1.2 Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
touch requirements.txt
```

**requirements.txt**:
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
anthropic>=0.18.0
ollama>=0.1.6
chromadb>=0.4.22
fastmcp>=0.2.0
pydantic>=2.5.3
pydantic-settings>=2.1.0
httpx>=0.26.0
beautifulsoup4>=4.12.3
robotexclusionrulesparser>=1.7.0
PyYAML>=6.0.1
```

### 1.3 Configuration System
- Create `core/config.py` with Pydantic Settings
- Create `config.yaml` with defaults
- Create `core/config_manager.py` for runtime updates

### 1.4 ChromaDB Setup
- Create `services/vectordb.py`
- Implement dual collection architecture
- Create `services/embeddings.py` with Ollama

**Checkpoint**: Can initialize ChromaDB and generate embeddings

## Phase 2: MCP Server

### 2.1 MCP Server Skeleton
- Create `mcp_server/server.py` with FastMCP
- Setup basic server structure

### 2.2 Memory Tools
- Implement `memory_store(user_id, content, metadata)`
- Implement `memory_lookup(user_id, query, limit=5)`
- Use ChromaDB collection per user: `memories_{user_id}`

### 2.3 Knowledge Tools
- Implement `knowledge_store(content, url, metadata)`
- Implement `knowledge_search(query, limit=5, rerank=True)`
- Implement `knowledge_delete(url)`
- Use global ChromaDB collection: `knowledge_global`

### 2.4 Reranking
- Create `services/reranker.py`
- Implement Ollama-based reranking for knowledge_search

**Checkpoint**: MCP server runs, tools can be called directly

## Phase 3: Agents

### 3.1 Research Agent
**File**: `agents/research_agent.py`

```python
class ResearchAgent:
    def __init__(self, anthropic_api_key, mcp_tools):
        self.client = Anthropic(api_key=anthropic_api_key)
        self.tools = mcp_tools

    async def stream_chat(self, user_id, message, session_id):
        # Use Anthropic messages API with streaming
        # Yield SSE events: text, tool_use, tool_result, done
        pass
```

Features:
- Stream responses from Claude
- Convert MCP tools to Anthropic tool format
- Handle tool calls
- Emit SSE events

### 3.2 Crawler Agent
**File**: `agents/crawler_agent.py`

Based on `/Users/suraj-devloper/workspace/code-context/src/crawler.py`:
- Add robots.txt parsing
- Ollama-based link filtering
- User steering queue
- Progress tracking

```python
class CrawlerAgent:
    async def crawl_with_steering(self, url, intent, user_feedback_queue):
        # Discover links
        # Filter with Ollama
        # Emit steering_needed events
        # Wait for user approval
        # Crawl and store
        pass
```

**Checkpoint**: Agents can run independently

## Phase 4: API Routes

### 4.1 FastAPI App
**File**: `api/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AgentX API")
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

### 4.2 Research Routes
**File**: `api/research.py`

```python
@router.post("/research/chat")
async def research_chat(request: ChatRequest):
    # Return SSE stream
    return EventSourceResponse(agent.stream_chat(...))

@router.get("/research/sessions/{user_id}")
async def list_sessions(user_id: str):
    pass
```

### 4.3 Crawler Routes
**File**: `api/crawler.py`

```python
@router.post("/crawler/start")
async def start_crawl(request: CrawlRequest):
    # Create background job
    # Return job_id and SSE URL
    pass

@router.get("/crawler/jobs/{job_id}/stream")
async def crawl_stream(job_id: str):
    # Return SSE stream
    pass

@router.post("/crawler/jobs/{job_id}/steer")
async def steer_crawl(job_id: str, decision: SteerDecision):
    pass
```

### 4.4 Knowledge & Memory Routes
**File**: `api/knowledge.py`, `api/memory.py`

Basic CRUD operations for knowledge and memory.

### 4.5 Config Routes
**File**: `api/config.py`

```python
@router.get("/config")
async def get_config():
    return config_manager.get_config()

@router.put("/config")
async def update_config(updates: dict):
    return config_manager.update_config(updates)
```

**Checkpoint**: All API routes return data, SSE streams work

## Phase 5: Frontend

### 5.1 Next.js Setup
```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --app
npx shadcn-ui@latest init
```

### 5.2 Install Dependencies
```bash
npm install @tanstack/react-query zustand axios react-hook-form zod
npx shadcn-ui@latest add button card input label tabs textarea
```

### 5.3 Create Hooks
**File**: `hooks/useSSE.ts`

```typescript
export function useSSE(url: string, onEvent: (event) => void) {
  useEffect(() => {
    const eventSource = new EventSource(url)
    eventSource.onmessage = (e) => onEvent(JSON.parse(e.data))
    return () => eventSource.close()
  }, [url])
}
```

### 5.4 Research Page
**File**: `app/(dashboard)/research/page.tsx`

Components:
- `ChatInterface` - Message list with streaming
- `ToolUseCard` - Show tool invocations
- `MemoryPanel` - List memories

### 5.5 Crawler Page
**File**: `app/(dashboard)/crawler/page.tsx`

Components:
- `CrawlerConfig` - URL, intent, settings
- `ProgressView` - Live progress with SSE
- `SteeringPanel` - Approve/reject links

### 5.6 Knowledge Page
**File**: `app/(dashboard)/knowledge/page.tsx`

Components:
- `KnowledgeGrid` - List all knowledge entries
- `SearchBar` - Semantic search
- `DeleteButton` - Bulk delete

### 5.7 Settings Page
**File**: `app/(dashboard)/settings/page.tsx`

Components:
- `ConfigForm` - Form editor with validation
- `ConfigEditor` - JSON editor
- Tabs to switch between modes

**Checkpoint**: Full UI works end-to-end

## Phase 6: Scripts & Testing

### 6.1 Create Scripts
- `scripts/setup.sh` - Install dependencies, pull Ollama models
- `scripts/start.sh` - Start MCP, API, frontend
- `scripts/stop.sh` - Stop all services
- `scripts/dev.sh` - Development mode

### 6.2 Create Makefile
```makefile
setup:
	./scripts/setup.sh
start:
	./scripts/start.sh
stop:
	./scripts/stop.sh
dev:
	./scripts/dev.sh
```

### 6.3 Testing
- Test MCP tools independently
- Test each agent
- Test API endpoints
- Test UI components
- End-to-end flow tests

**Checkpoint**: System works end-to-end

## Phase 7: Documentation & Polish

- Update docs with any architecture changes
- Add code examples to technical-reference.md
- Create README.md with quick start
- Fix bugs found during testing

## Timeline Estimate

- Phase 1: 2 hours
- Phase 2: 4 hours
- Phase 3: 6 hours
- Phase 4: 4 hours
- Phase 5: 8 hours
- Phase 6: 3 hours
- Phase 7: 2 hours

**Total**: ~29 hours for initial working version
