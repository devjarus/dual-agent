# Technical Reference

## MCP Tools

### Memory Tools

#### memory_store
```python
async def memory_store(user_id: str, content: str, metadata: dict = {}) -> dict
```
Store a memory for a specific user.

**Returns**: `{"status": "success", "id": "mem_xxx"}`

**Example**:
```python
result = await memory_store(
    user_id="user_123",
    content="User prefers dark mode",
    metadata={"category": "preference", "source": "chat"}
)
```

#### memory_lookup
```python
async def memory_lookup(user_id: str, query: str, limit: int = 5) -> list
```
Semantic search in user's memories.

**Returns**: List of `{"id": str, "content": str, "score": float, "metadata": dict}`

**Example**:
```python
results = await memory_lookup(
    user_id="user_123",
    query="user preferences",
    limit=5
)
```

### Knowledge Tools

#### knowledge_store
```python
async def knowledge_store(content: str, url: str, metadata: dict = {}) -> dict
```
Store content in global knowledge base.

**Returns**: `{"status": "success", "chunks": int}`

**Example**:
```python
result = await knowledge_store(
    content="RAG is Retrieval Augmented Generation...",
    url="https://example.com/rag",
    metadata={"title": "RAG Overview", "domain": "example.com"}
)
```

#### knowledge_search
```python
async def knowledge_search(query: str, limit: int = 5, rerank: bool = True) -> list
```
Search knowledge base with optional Ollama reranking.

**Returns**: List of `{"id": str, "content": str, "score": float, "url": str, "metadata": dict}`

**Example**:
```python
results = await knowledge_search(
    query="what is RAG",
    limit=5,
    rerank=True
)
```

#### knowledge_delete
```python
async def knowledge_delete(url: str) -> dict
```
Delete all knowledge entries for a URL.

**Returns**: `{"status": "success", "deleted": int}`

---

## API Endpoints

### Research Agent

#### POST /api/research/chat
Stream chat with Research Agent.

**Request**:
```json
{
  "user_id": "user_123",
  "message": "What is RAG?",
  "session_id": "session_456"
}
```

**Response**: SSE stream
```
event: text
data: {"chunk": "RAG is"}

event: tool_use
data: {"tool": "knowledge_search", "args": {"query": "RAG"}}

event: tool_result
data: {"result": [...]}

event: text
data: {"chunk": " Retrieval Augmented Generation"}

event: done
data: {"session_id": "session_456"}
```

#### GET /api/research/sessions/{user_id}
List chat sessions.

**Response**:
```json
{
  "sessions": [
    {"id": "session_456", "created_at": "2024-01-15T10:00:00Z", "message_count": 5}
  ]
}
```

### Crawler Agent

#### POST /api/crawler/start
Start a crawl job.

**Request**:
```json
{
  "url": "https://docs.example.com",
  "intent": "API documentation only",
  "max_depth": 3,
  "max_pages": 50,
  "user_id": "user_123"
}
```

**Response**:
```json
{
  "job_id": "job_789",
  "status": "started",
  "stream_url": "/api/crawler/jobs/job_789/stream"
}
```

#### GET /api/crawler/jobs/{job_id}/stream
Stream crawl progress.

**Response**: SSE stream
```
event: discovered
data: {"links": ["url1", "url2"], "count": 25}

event: crawling
data: {"url": "url1", "progress": 0.1}

event: steering_needed
data: {"link": "url3", "reasoning": "...", "approve_reject": null}

event: stored
data: {"url": "url1", "chunks": 5}

event: completed
data: {"total_pages": 20, "total_chunks": 100}
```

#### POST /api/crawler/jobs/{job_id}/steer
Approve/reject a link during crawling.

**Request**:
```json
{
  "link": "https://docs.example.com/advanced",
  "approved": true
}
```

### Knowledge Management

#### GET /api/knowledge
List knowledge entries.

**Query params**: `search`, `limit`, `offset`

**Response**:
```json
{
  "entries": [
    {"id": "xxx", "url": "...", "title": "...", "chunk_count": 5}
  ],
  "total": 100
}
```

#### DELETE /api/knowledge
Bulk delete.

**Request**:
```json
{
  "urls": ["https://example.com/page1", "https://example.com/page2"]
}
```

### Memory Management

#### GET /api/memory/{user_id}
List user memories.

#### DELETE /api/memory/{user_id}/{memory_id}
Delete specific memory.

### Configuration

#### GET /api/config
Get current configuration.

**Response**: Full config object

#### PUT /api/config
Update configuration.

**Request**:
```json
{
  "updates": {
    "crawler": {
      "max_depth": 5
    }
  },
  "validate": true
}
```

#### POST /api/config/reset
Reset to defaults.

---

## Configuration Options

### config.yaml

```yaml
anthropic:
  api_key: ${ANTHROPIC_API_KEY}  # From env
  model: claude-3-5-sonnet-20241022
  max_tokens: 4096
  temperature: 0.7

ollama:
  base_url: http://localhost:11434
  embedding_model: nomic-embed-text
  chat_model: llama3.1
  temperature: 0.7
  timeout: 120

crawler:
  max_depth: 3                    # 1-10
  max_pages: 100                  # 1-1000
  delay_between_requests: 1.0     # seconds, 0.5-10
  respect_robots_txt: true
  timeout: 30
  user_agent: AgentX-Crawler/1.0

vectordb:
  persist_directory: ./data/chroma
  chunk_size: 512                 # tokens, 128-2048
  chunk_overlap: 50               # tokens

mcp_server:
  host: localhost
  port: 8001

api:
  host: 0.0.0.0
  port: 8000
  cors_origins:
    - http://localhost:3000
  log_level: info
```

---

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your_key_here

# Optional (have defaults)
OLLAMA_BASE_URL=http://localhost:11434
CHROMA_PERSIST_DIR=./data/chroma
API_HOST=0.0.0.0
API_PORT=8000
MCP_HOST=localhost
MCP_PORT=8001
```

---

## SSE Event Schemas

### Research Agent Events

**text**:
```json
{"type": "text", "chunk": "string"}
```

**tool_use**:
```json
{
  "type": "tool_use",
  "tool": "knowledge_search",
  "args": {"query": "...", "limit": 5}
}
```

**tool_result**:
```json
{
  "type": "tool_result",
  "result": [...]
}
```

**done**:
```json
{"type": "done", "session_id": "session_456"}
```

### Crawler Agent Events

**discovered**:
```json
{"type": "discovered", "links": ["url1", "url2"], "count": 25}
```

**crawling**:
```json
{"type": "crawling", "url": "url1", "progress": 0.4}
```

**steering_needed**:
```json
{
  "type": "steering_needed",
  "link": "url3",
  "reasoning": "Link may be off-topic",
  "waiting": true
}
```

**stored**:
```json
{"type": "stored", "url": "url1", "chunks": 5}
```

**completed**:
```json
{
  "type": "completed",
  "total_pages": 20,
  "total_chunks": 100,
  "duration": 45.2
}
```

---

## CLI Commands

```bash
# Setup
make setup          # One-time setup (install deps, pull models)

# Start/Stop
make start          # Start all services
make stop           # Stop all services
make dev            # Development mode with auto-reload

# Utilities
make test           # Run tests
make health         # Check service health
make logs           # Tail logs
make clean          # Clean build artifacts
```

---

## ChromaDB Collections

### memories_{user_id}
Per-user memory storage.

**Metadata**:
- `user_id`: string
- `created_at`: ISO timestamp
- `source`: string (e.g., "chat", "manual")
- `category`: string (optional)

### knowledge_global
Global knowledge base.

**Metadata**:
- `url`: string (unique per document)
- `title`: string
- `chunk_index`: int
- `total_chunks`: int
- `domain`: string
- `crawl_date`: ISO timestamp
