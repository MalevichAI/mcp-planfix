"""Configuration management for Planfix MCP Server."""

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class PlanfixConfig(BaseSettings):
    """Configuration for Planfix API."""
    model_config = {'extra': 'allow'}
    
    # Required Planfix API credentials
    planfix_account: str | None = None
    planfix_api_key: str | None = None
    
    # Optional configuration
    planfix_base_url: Optional[str] = None
    request_timeout: int = 30
    debug: bool = False
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }
    
    @model_validator(mode='before')
    @classmethod
    def build_base_url(cls, values):
        """Build base URL if not provided."""
        if isinstance(values, dict):
            base_url = values.get("planfix_base_url")
            if base_url is not None:
                values["planfix_base_url"] = base_url.rstrip("/")
            else:
                account = values.get("planfix_account")
                if not account:
                    raise ValueError("planfix_account is required")
                values["planfix_base_url"] = f"https://{account}.planfix.ru"
        return values
    
    @field_validator("planfix_account")
    @classmethod
    def validate_account(cls, v: str) -> str:
        """Validate account name."""
        if not v:
            raise ValueError("PLANFIX_ACCOUNT environment variable is required")
        return v.strip()
    
    @field_validator("planfix_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key."""
        if not v:
            raise ValueError("PLANFIX_API_KEY environment variable is required")
        return v.strip()
    



def get_config() -> PlanfixConfig:
    """Get validated configuration."""
    try:
        return PlanfixConfig()
    except Exception as e:
        raise RuntimeError(
            f"Failed to load configuration: {e}\n"
            "Please check your .env file or environment variables."
        ) from e


# Global config instance
config = get_config()