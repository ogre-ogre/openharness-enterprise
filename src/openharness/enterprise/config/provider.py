"""
OpenHarness Enterprise - Provider Configuration

LLM provider configuration for the enterprise server.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

# Load .env file if exists
try:
    from dotenv import load_dotenv
    # Try to find .env in multiple locations
    env_paths = [
        Path(__file__).parent.parent.parent.parent / ".env",  # project root
        Path.cwd() / ".env",  # current working directory
        Path.home() / ".oh-enterprise" / ".env",  # user config
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"[Config] Loaded .env from: {env_path}")
            break
except ImportError:
    pass


class ProviderConfig(BaseModel):
    """LLM Provider configuration."""
    
    # Provider type: 'anthropic' | 'openai' | 'openai-compatible'
    provider: str = "anthropic"
    
    # API key (can also be set via environment variable)
    api_key: Optional[str] = None
    
    # Base URL for compatible providers
    base_url: Optional[str] = None
    
    # Model name
    model: str = "glm-5"
    
    # Max tokens
    max_tokens: int = 4096
    
    # Temperature
    temperature: float = 0.7


# Default configuration from environment variables
DEFAULT_PROVIDER = ProviderConfig(
    provider=os.getenv("OH_PROVIDER", "anthropic"),
    api_key=os.getenv("OH_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"),
    base_url=os.getenv("OH_BASE_URL") or os.getenv("ANTHROPIC_BASE_URL"),
    model=os.getenv("OH_MODEL") or os.getenv("ANTHROPIC_MODEL", "glm-5"),
)


def get_provider_config() -> ProviderConfig:
    """Get current provider configuration."""
    return DEFAULT_PROVIDER


def set_provider_config(config: ProviderConfig) -> None:
    """Set provider configuration."""
    global DEFAULT_PROVIDER
    DEFAULT_PROVIDER = config