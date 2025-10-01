"""Tests for configuration management."""

import pytest
from pathlib import Path

from backend.core.config import (
    Settings,
    AnthropicConfig,
    OllamaConfig,
    CrawlerConfig,
    VectorDBConfig,
    MCPServerConfig,
    APIConfig,
)


@pytest.mark.unit
class TestAnthropicConfig:
    """Tests for Anthropic configuration."""

    def test_anthropic_config_defaults(self, test_env_vars):
        """Test Anthropic config with defaults."""
        config = AnthropicConfig()

        assert config.model == "claude-3-5-sonnet-20241022"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.api_key == "test-anthropic-key"

    def test_anthropic_config_custom_values(self, test_env_vars):
        """Test Anthropic config with custom values."""
        config = AnthropicConfig(
            model="claude-3-opus",
            max_tokens=8192,
            temperature=0.5,
        )

        assert config.model == "claude-3-opus"
        assert config.max_tokens == 8192
        assert config.temperature == 0.5


@pytest.mark.unit
class TestCrawlerConfig:
    """Tests for Crawler configuration."""

    def test_crawler_config_defaults(self):
        """Test crawler config with defaults."""
        config = CrawlerConfig()

        assert config.max_depth == 3
        assert config.max_pages == 100
        assert config.delay_between_requests == 1.0
        assert config.respect_robots_txt is True
        assert config.timeout == 30
        assert config.user_agent == "AgentX-Crawler/1.0"

    def test_crawler_config_validation(self):
        """Test crawler config validation."""
        # Valid values
        config = CrawlerConfig(max_depth=5, max_pages=50)
        assert config.max_depth == 5
        assert config.max_pages == 50

        # Test bounds
        with pytest.raises(Exception):  # Pydantic ValidationError
            CrawlerConfig(max_depth=11)  # Max is 10

        with pytest.raises(Exception):
            CrawlerConfig(max_pages=1001)  # Max is 1000


@pytest.mark.unit
class TestVectorDBConfig:
    """Tests for VectorDB configuration."""

    def test_vectordb_config_defaults(self):
        """Test vectordb config with defaults."""
        config = VectorDBConfig()

        assert config.persist_directory == "./data/chroma"
        assert config.chunk_size == 512
        assert config.chunk_overlap == 50

    def test_vectordb_config_validation(self):
        """Test vectordb config validation."""
        # Valid values
        config = VectorDBConfig(chunk_size=1024, chunk_overlap=100)
        assert config.chunk_size == 1024
        assert config.chunk_overlap == 100

        # Test bounds
        with pytest.raises(Exception):  # Pydantic ValidationError
            VectorDBConfig(chunk_size=64)  # Min is 128

        with pytest.raises(Exception):
            VectorDBConfig(chunk_size=4096)  # Max is 2048


@pytest.mark.unit
class TestSettings:
    """Tests for main Settings class."""

    def test_settings_from_yaml(self, temp_config_file, test_env_vars):
        """Test loading settings from YAML."""
        settings = Settings.from_yaml(temp_config_file)

        # Check all sections loaded
        assert settings.anthropic is not None
        assert settings.ollama is not None
        assert settings.crawler is not None
        assert settings.vectordb is not None
        assert settings.mcp_server is not None
        assert settings.api is not None

        # Check specific values
        assert settings.anthropic.model == "claude-3-5-sonnet-20241022"
        assert settings.crawler.max_depth == 3
        assert settings.vectordb.chunk_size == 512

    def test_settings_to_yaml(self, temp_config_file, test_env_vars, tmp_path):
        """Test saving settings to YAML."""
        settings = Settings.from_yaml(temp_config_file)

        # Modify a value
        settings.crawler.max_depth = 5

        # Save to new file
        output_file = tmp_path / "output_config.yaml"
        settings.to_yaml(str(output_file))

        # Load and verify
        new_settings = Settings.from_yaml(str(output_file))
        assert new_settings.crawler.max_depth == 5

    def test_settings_env_override(self, temp_config_file, monkeypatch):
        """Test that environment variables override YAML."""
        # Set env var
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-override-key")
        monkeypatch.setenv("API_PORT", "9000")

        settings = Settings.from_yaml(temp_config_file)

        # Env var should override
        assert settings.anthropic.api_key == "env-override-key"
        assert settings.api.port == 9000
