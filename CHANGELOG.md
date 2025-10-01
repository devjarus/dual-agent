# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure with docs, backend, frontend, and scripts
- Documentation: architecture.md, implementation-plan.md, technical-reference.md
- Development scripts: setup.sh, start.sh, stop.sh, dev.sh, test.sh, health-check.sh
- Configuration system with config.yaml and .env support
- Makefile for easy command access
- Development workflow documentation (CLAUDE.md, .cursor/rules/project-workflow.mdc)
- ChromaDB service with dual collections (per-user memories, global knowledge)
- MCP server with memory tools (memory_store, memory_lookup)
- MCP server with knowledge tools (knowledge_store, knowledge_search, knowledge_delete)
- Pydantic configuration management with YAML and environment variable support
- Research Agent with Claude streaming and MCP tool integration
- Crawler Agent with Ollama-powered link filtering and user steering
- Web scraping utilities with robots.txt support
- Comprehensive testing infrastructure with pytest
- Unit tests for configuration and ChromaDB service
- Pre-commit hooks for code quality and testing
- Test coverage reporting

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.1.0] - 2024-01-01

### Added
- Initial release
- Project foundation and structure

---

## Changelog Guidelines

### Categories
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security-related changes

### When to Update
Update CHANGELOG.md when you:
- Add a new feature (feat commits)
- Fix a bug (fix commits)
- Make breaking changes
- Deprecate or remove functionality
- Make security improvements

### How to Update
1. Add entry under `[Unreleased]` section
2. Use appropriate category (Added, Changed, etc.)
3. Write user-facing description (not technical implementation details)
4. Keep entries concise and clear

### Example Entry
```markdown
### Added
- Research agent with Claude streaming and tool use visualization
- Crawler agent with Ollama-powered link filtering and user steering
- MCP server with memory_store, memory_lookup, knowledge_store, knowledge_search tools
```

### Version Releases
When releasing a version:
1. Move unreleased items to new version section
2. Add version number and date
3. Create new empty `[Unreleased]` section
