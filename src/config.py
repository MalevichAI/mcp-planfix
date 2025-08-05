"""Configuration management for Planfix MCP Server."""

from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, field_validator, model_validator

# Load environment variables from .env file
load_dotenv()


class PlanfixConfig(BaseModel):
    """Configuration for Planfix API."""
    model_config = {'extra': 'allow'}
    
    # Required Planfix API credentials
    planfix_account: str | None = None
    planfix_api_key: str | None = None
    
    request_timeout: int = 30
    debug: bool = False

    


def get_config() -> PlanfixConfig:
    """Get validated configuration."""
    return PlanfixConfig()

# Global config instance
config = get_config()