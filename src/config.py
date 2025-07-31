"""Configuration management for Planfix MCP Server."""

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseSettings, validator

# Load environment variables from .env file
load_dotenv()


class PlanfixConfig(BaseSettings):
    """Configuration for Planfix API."""
    
    # Required Planfix API credentials
    planfix_account: str
    planfix_api_key: str
    planfix_user_key: str
    
    # Optional configuration
    planfix_base_url: Optional[str] = None
    request_timeout: int = 30
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    @validator("planfix_base_url", pre=True, always=True)
    def build_base_url(cls, v: Optional[str], values: dict) -> str:
        """Build base URL if not provided."""
        if v is not None:
            return v.rstrip("/")
        
        account = values.get("planfix_account")
        if not account:
            raise ValueError("planfix_account is required")
            
        return f"https://{account}.planfix.ru"
    
    @validator("planfix_account")
    def validate_account(cls, v: str) -> str:
        """Validate account name."""
        if not v:
            raise ValueError("PLANFIX_ACCOUNT environment variable is required")
        return v.strip()
    
    @validator("planfix_api_key")
    def validate_api_key(cls, v: str) -> str:
        """Validate API key."""
        if not v:
            raise ValueError("PLANFIX_API_KEY environment variable is required")
        return v.strip()
    
    @validator("planfix_user_key")
    def validate_user_key(cls, v: str) -> str:
        """Validate user key."""
        if not v:
            raise ValueError("PLANFIX_USER_KEY environment variable is required")
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