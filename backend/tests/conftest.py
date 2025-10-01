"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path

import pytest

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_content = """
anthropic:
  api_key: test-key
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
  max_depth: 3
  max_pages: 100
  delay_between_requests: 1.0
  respect_robots_txt: true
  timeout: 30
  user_agent: AgentX-Crawler/1.0

vectordb:
  persist_directory: ./test_data/chroma
  chunk_size: 512
  chunk_overlap: 50

mcp_server:
  host: localhost
  port: 8001

api:
  host: 0.0.0.0
  port: 8000
  cors_origins:
    - http://localhost:3000
  log_level: info
"""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(config_content)
    return str(config_file)


@pytest.fixture
def test_env_vars(monkeypatch):
    """Set test environment variables."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("CHROMA_PERSIST_DIR", "./test_data/chroma")


@pytest.fixture
def chroma_test_dir(tmp_path):
    """Create a temporary ChromaDB directory for testing."""
    chroma_dir = tmp_path / "chroma_test"
    chroma_dir.mkdir()
    return str(chroma_dir)
