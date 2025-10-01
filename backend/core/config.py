"""Configuration management using Pydantic Settings."""

import os
from pathlib import Path
from typing import List

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnthropicConfig(BaseSettings):
    """Anthropic API configuration."""

    api_key: str = Field(alias="ANTHROPIC_API_KEY")
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.7


class OllamaConfig(BaseSettings):
    """Ollama configuration."""

    base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    embedding_model: str = "nomic-embed-text"
    chat_model: str = "llama3.1"
    temperature: float = 0.7
    timeout: int = 120


class CrawlerConfig(BaseSettings):
    """Crawler configuration."""

    max_depth: int = Field(default=3, ge=1, le=10)
    max_pages: int = Field(default=100, ge=1, le=1000)
    delay_between_requests: float = Field(default=1.0, ge=0.5, le=10.0)
    respect_robots_txt: bool = True
    timeout: int = 30
    user_agent: str = "AgentX-Crawler/1.0"


class VectorDBConfig(BaseSettings):
    """Vector database configuration."""

    persist_directory: str = Field(
        default="./data/chroma", alias="CHROMA_PERSIST_DIR"
    )
    chunk_size: int = Field(default=512, ge=128, le=2048)
    chunk_overlap: int = 50


class MCPServerConfig(BaseSettings):
    """MCP server configuration."""

    host: str = Field(default="localhost", alias="MCP_HOST")
    port: int = Field(default=8001, alias="MCP_PORT")


class APIConfig(BaseSettings):
    """API server configuration."""

    host: str = Field(default="0.0.0.0", alias="API_HOST")
    port: int = Field(default=8000, alias="API_PORT")
    cors_origins: List[str] = ["http://localhost:3000"]
    log_level: str = "info"


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    anthropic: AnthropicConfig = Field(default_factory=AnthropicConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    vectordb: VectorDBConfig = Field(default_factory=VectorDBConfig)
    mcp_server: MCPServerConfig = Field(default_factory=MCPServerConfig)
    api: APIConfig = Field(default_factory=APIConfig)

    @classmethod
    def from_yaml(cls, yaml_path: str = "backend/config.yaml") -> "Settings":
        """Load settings from YAML file and environment variables.

        Environment variables take precedence over YAML values.
        """
        # Load YAML config
        config_path = Path(yaml_path)
        if config_path.exists():
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f) or {}
        else:
            yaml_config = {}

        # Create nested config objects
        settings_dict = {}

        # Process each section
        for section in [
            "anthropic",
            "ollama",
            "crawler",
            "vectordb",
            "mcp_server",
            "api",
        ]:
            section_data = yaml_config.get(section, {})
            settings_dict[section] = section_data

        return cls(**settings_dict)

    def to_yaml(self, yaml_path: str = "backend/config.yaml") -> None:
        """Save current settings to YAML file.

        Note: Does not save environment-only values like API keys.
        """
        config_dict = {
            "anthropic": {
                "api_key": "${ANTHROPIC_API_KEY}",  # Don't save actual key
                "model": self.anthropic.model,
                "max_tokens": self.anthropic.max_tokens,
                "temperature": self.anthropic.temperature,
            },
            "ollama": {
                "base_url": self.ollama.base_url,
                "embedding_model": self.ollama.embedding_model,
                "chat_model": self.ollama.chat_model,
                "temperature": self.ollama.temperature,
                "timeout": self.ollama.timeout,
            },
            "crawler": {
                "max_depth": self.crawler.max_depth,
                "max_pages": self.crawler.max_pages,
                "delay_between_requests": self.crawler.delay_between_requests,
                "respect_robots_txt": self.crawler.respect_robots_txt,
                "timeout": self.crawler.timeout,
                "user_agent": self.crawler.user_agent,
            },
            "vectordb": {
                "persist_directory": self.vectordb.persist_directory,
                "chunk_size": self.vectordb.chunk_size,
                "chunk_overlap": self.vectordb.chunk_overlap,
            },
            "mcp_server": {
                "host": self.mcp_server.host,
                "port": self.mcp_server.port,
            },
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "cors_origins": self.api.cors_origins,
                "log_level": self.api.log_level,
            },
        }

        config_path = Path(yaml_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.from_yaml()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from YAML and environment."""
    global _settings
    _settings = Settings.from_yaml()
    return _settings
