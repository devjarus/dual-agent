# AgentX v1-Prototype Development Guide

Instructions for AI coding agents developing the AgentX dual-agent system.

## 1. Coding Philosophy

### Iterative Development
- **Small Steps:** Work incrementally with verifiable changes
- **Test Critical Paths:** Write tests for agents, MCP tools, API endpoints
- **Simplest Solution First:** Avoid over-engineering

### SOLID Principles
- **Single Responsibility:** One purpose per class/function
- **Open/Closed:** Open for extension, closed for modification
- **Dependency Inversion:** Depend on abstractions, not implementations

### Simplicity & Clarity
- **KISS:** Keep it simple
- **YAGNI:** Don't add features until needed
- **Meaningful Names:** Descriptive variables, functions, classes
- **Minimal Comments:** Explain *why*, not *what*

## 2. Grounding Documents

**All development must align with project design documents.**

### Required Reading Before Coding
- **`docs/architecture.md`** - System design, components, data flows
- **`docs/implementation-plan.md`** - Phase-by-phase build guide
- **`docs/technical-reference.md`** - API specs, tool signatures, events

**These docs are the source of truth. Always consult them before implementing.**

## 3. Development Workflow

### For Any Task (Feature, Bug Fix, Refactoring):

#### Step 1: Analyze and Plan
1. Understand the user's request
2. Read relevant sections in `docs/`
3. Examine existing code for patterns
4. Create a TODO list (use TodoWrite tool)

#### Step 2: Implement
1. Write code following the implementation plan
2. Write tests for critical functionality
3. Run `make test` to verify
4. Manually test with `make dev`

#### Step 3: Update Documentation & Changelog
**CRITICAL: See section 4 for documentation sync rules.**

Update immediately after code changes:
- `docs/architecture.md` for architectural changes
- `docs/technical-reference.md` for API/tool/config changes
- `CHANGELOG.md` for user-facing changes

#### Step 4: Verify
1. Run `make test`
2. Start services: `make dev`
3. Test in browser/API

#### Step 5: Commit (When Applicable)
Use conventional commits:
```
<type>[scope]: <description>

[optional body]
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

**Example:**
```
feat(crawler): add link steering with user approval

Implements steering queue allowing users to approve/reject
uncertain links during crawling.
```

## 4. Documentation & Changelog Sync Rules

**Keep docs and changelog synchronized with code changes.**

### What to Update When

| Change Type | Update |
|-------------|--------|
| Add/modify component/agent | `architecture.md` + `CHANGELOG.md` |
| Change data flow | `architecture.md` |
| Add/modify API endpoint | `technical-reference.md` + `CHANGELOG.md` |
| Add/modify MCP tool | `technical-reference.md` + `CHANGELOG.md` |
| Add/modify SSE event | `technical-reference.md` |
| Change config options | `technical-reference.md` + `CHANGELOG.md` |
| Adjust build phases | `implementation-plan.md` |
| User-facing feature/fix | `CHANGELOG.md` |
| Major refactor | Review ALL docs |

### Changelog Guidelines

**When to update CHANGELOG.md:**
- New features → `[Unreleased]` → `Added`
- Bug fixes → `[Unreleased]` → `Fixed`
- Breaking changes → `[Unreleased]` → `Changed`
- Deprecations → `[Unreleased]` → `Deprecated`
- Removals → `[Unreleased]` → `Removed`

**How to update:**
1. Add entry under `[Unreleased]` section
2. Use appropriate category
3. Write user-facing description (not implementation details)
4. Keep it concise

**Example:**
```markdown
## [Unreleased]

### Added
- Research agent with Claude streaming and tool use visualization

### Fixed
- ChromaDB connection timeout on first startup
```

### Documentation Principles
- **Lightweight** - Brief and code-focused
- **Always Current** - Update with every change
- **No Status** - Docs reflect design, not progress

## 5. Project Architecture

### System Overview
- **Research Agent** - Claude (Anthropic) with streaming + tool use
- **Crawler Agent** - Ollama-powered crawler with user steering
- **MCP Server** - Memory (per-user) and knowledge (global) tools
- **ChromaDB** - Dual collections for isolation and sharing
- **Frontend** - Next.js 15 with SSE streaming

**For details:** See `docs/architecture.md`

### Tech Stack
- **Backend:** FastAPI, FastMCP, Anthropic SDK, Ollama, ChromaDB
- **Frontend:** Next.js 15, shadcn/ui, TanStack Query
- **Streaming:** Server-Sent Events
- **Config:** Pydantic + YAML with runtime updates

## 6. Service Management

### Quick Commands
```bash
make setup    # One-time setup
make start    # Start all services
make stop     # Stop all
make dev      # Dev mode with tmux
make test     # Run tests
make health   # Health check
```

### Dependencies
- **Ollama** - For embeddings and crawler LLM (must be running)
- **ChromaDB** - Auto-started, persists to `data/chroma`
- **Anthropic API** - Requires key in `.env`

## 7. Common Tasks

### Add MCP Tool
1. Edit `backend/mcp_server/{memory,knowledge}_tools.py`
2. Use `@mcp.tool()` decorator
3. Update `docs/technical-reference.md` with signature
4. Update `CHANGELOG.md` under `[Unreleased]` → `Added`
5. Test manually

### Add API Endpoint
1. Add route in `backend/api/{research,crawler,knowledge,memory,config}.py`
2. Use Pydantic models
3. Update `docs/technical-reference.md` with endpoint spec
4. Update `CHANGELOG.md` if user-facing
5. Test at http://localhost:8000/docs

### Add Frontend Component
1. Place in `frontend/src/components/{feature}/`
2. Use shadcn/ui components
3. For streaming, use `useSSE` hook
4. Update `CHANGELOG.md` if user-facing
5. Test in browser

### Modify Config
1. Update `backend/core/config.py` (Pydantic)
2. Update `backend/config.yaml` (defaults)
3. Update `docs/technical-reference.md` config section
4. Update `CHANGELOG.md` under `[Unreleased]` → `Changed`

## 8. Testing

### What to Test
- MCP tools functionality
- API endpoint request/response
- Agent streaming and tool calls
- Critical UI flows

### Run Tests
```bash
make test                          # All
cd backend && pytest tests/        # Backend
cd frontend && npm test            # Frontend
```

## 9. Important Notes

### ChromaDB Collections
- `memories_{user_id}` - Per-user isolation
- `knowledge_global` - Shared knowledge
- Auto-created on first use

### Streaming Best Practices
- Close streams properly
- Handle reconnection in frontend
- Emit progress for long operations
- Use typed events

### Config Management
- Runtime updates save to YAML
- Pydantic validates changes
- UI edits via Settings page
- Env vars override config

## 10. Research, Testing & References

### Using Exa for Code Research
**Tool:** `mcp__exa__get_code_context_exa`

Search for implementation patterns and library documentation:
- `mcp__exa__get_code_context_exa("FastAPI SSE streaming")`
- `mcp__exa__get_code_context_exa("ChromaDB Python client examples")`
- `mcp__exa__get_code_context_exa("Anthropic SDK streaming tool use")`
- `mcp__exa__get_code_context_exa("Next.js 15 EventSource SSE")`

Use specific queries with library/framework names.

### Using Chrome DevTools MCP for UI Testing
**Available tools:**
- `mcp__chrome-devtools__take_snapshot` - Page structure
- `mcp__chrome-devtools__click(uid)` - Click elements
- `mcp__chrome-devtools__fill(uid, value)` - Fill forms
- `mcp__chrome-devtools__list_network_requests()` - API calls
- `mcp__chrome-devtools__list_console_messages()` - Console logs
- `mcp__chrome-devtools__take_screenshot()` - Screenshots

**Testing workflow:**
1. Start: `make dev`
2. Snapshot: Get page structure
3. Interact: Click, fill forms
4. Verify: Check network, console
5. Screenshot: Visual verification

**Use for:** Testing chat UI, crawler steering, SSE streams, config updates.

### Reference Implementations
- **RAG/Crawler:** `/Users/suraj-devloper/workspace/code-context`
- **UI/Frontend:** `/Users/suraj-devloper/workspace/ui-agentx`

## 11. Quick Reference

### Development Cycle
1. Read docs → Plan → Create TODOs
2. Implement → Test → Verify
3. **Update docs + CHANGELOG** → Commit

### Must Update
- Code change → Immediate doc update
- User-facing change → Update CHANGELOG.md
- Major refactor → Review all docs
- API/tool change → Update technical-reference.md

**Keep docs and changelog in sync. Always.**
