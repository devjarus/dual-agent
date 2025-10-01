"""Configuration API routes."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from backend.api.models import ConfigUpdateRequest, SuccessResponse
from backend.core.config import get_settings, reload_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_config() -> Dict[str, Any]:
    """Get current configuration.

    Example:
        GET /api/config
    """
    try:
        settings = get_settings()

        # Return configuration as dict
        config_dict = {
            "anthropic": {
                "model": settings.anthropic.model,
                "max_tokens": settings.anthropic.max_tokens,
                "temperature": settings.anthropic.temperature,
                # Don't return API key
            },
            "ollama": {
                "base_url": settings.ollama.base_url,
                "embedding_model": settings.ollama.embedding_model,
                "chat_model": settings.ollama.chat_model,
                "temperature": settings.ollama.temperature,
                "timeout": settings.ollama.timeout,
            },
            "crawler": {
                "max_depth": settings.crawler.max_depth,
                "max_pages": settings.crawler.max_pages,
                "delay_between_requests": settings.crawler.delay_between_requests,
                "respect_robots_txt": settings.crawler.respect_robots_txt,
                "timeout": settings.crawler.timeout,
                "user_agent": settings.crawler.user_agent,
            },
            "vectordb": {
                "persist_directory": settings.vectordb.persist_directory,
                "chunk_size": settings.vectordb.chunk_size,
                "chunk_overlap": settings.vectordb.chunk_overlap,
            },
            "mcp_server": {
                "host": settings.mcp_server.host,
                "port": settings.mcp_server.port,
            },
            "api": {
                "host": settings.api.host,
                "port": settings.api.port,
                "cors_origins": settings.api.cors_origins,
                "log_level": settings.api.log_level,
            },
        }

        return config_dict

    except Exception as e:
        logger.error(f"Failed to get config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/")
async def update_config(request: ConfigUpdateRequest) -> SuccessResponse:
    """Update configuration section.

    Updates are applied to runtime and saved to config.yaml.

    Example:
        PUT /api/config
        {
            "section": "crawler",
            "updates": {
                "max_depth": 5,
                "max_pages": 200
            }
        }
    """
    try:
        settings = get_settings()

        # Validate section
        valid_sections = [
            "anthropic",
            "ollama",
            "crawler",
            "vectordb",
            "mcp_server",
            "api",
        ]
        if request.section not in valid_sections:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid section. Must be one of: {valid_sections}",
            )

        # Get section object
        section = getattr(settings, request.section)

        # Apply updates
        for key, value in request.updates.items():
            if not hasattr(section, key):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid field '{key}' for section '{request.section}'",
                )

            # Update value
            setattr(section, key, value)

        # Save to YAML
        settings.to_yaml()

        logger.info(f"Updated config section '{request.section}': {request.updates}")

        return SuccessResponse(
            message=f"Configuration section '{request.section}' updated",
            data={"section": request.section, "updates": request.updates},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload")
async def reload_config() -> SuccessResponse:
    """Reload configuration from file.

    Example:
        POST /api/config/reload
    """
    try:
        reload_settings()

        logger.info("Configuration reloaded from file")

        return SuccessResponse(message="Configuration reloaded")

    except Exception as e:
        logger.error(f"Failed to reload config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_config() -> SuccessResponse:
    """Reset configuration to defaults.

    Creates a new config.yaml with default values.

    Example:
        POST /api/config/reset
    """
    try:
        # Create new settings with defaults
        from backend.core.config import Settings

        default_settings = Settings()

        # Save to YAML
        default_settings.to_yaml()

        # Reload
        reload_settings()

        logger.info("Configuration reset to defaults")

        return SuccessResponse(message="Configuration reset to defaults")

    except Exception as e:
        logger.error(f"Failed to reset config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate")
async def validate_config():
    """Validate current configuration.

    Checks if all required settings are present and valid.

    Example:
        GET /api/config/validate
    """
    try:
        settings = get_settings()

        issues = []

        # Check Anthropic API key
        if not settings.anthropic.api_key or settings.anthropic.api_key == "test-key":
            issues.append("Anthropic API key not set or using test key")

        # Check Ollama URL
        if not settings.ollama.base_url:
            issues.append("Ollama base URL not set")

        # Check persist directory
        from pathlib import Path

        persist_dir = Path(settings.vectordb.persist_directory)
        if not persist_dir.parent.exists():
            issues.append(f"Persist directory parent does not exist: {persist_dir.parent}")

        # Validation result
        is_valid = len(issues) == 0

        return {
            "valid": is_valid,
            "issues": issues,
            "message": "Configuration is valid" if is_valid else "Configuration has issues",
        }

    except Exception as e:
        logger.error(f"Failed to validate config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
