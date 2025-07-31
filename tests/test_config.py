"""Tests for configuration management."""

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from src.config import PlanfixConfig, get_config


class TestPlanfixConfig:
    """Test Planfix configuration class."""
    
    def test_config_with_all_required_fields(self):
        """Test config creation with all required fields."""
        config = PlanfixConfig(
            planfix_account="test-account",
            planfix_api_key="test-api-key",
            planfix_user_key="test-user-key"
        )
        
        assert config.planfix_account == "test-account"
        assert config.planfix_api_key == "test-api-key"
        assert config.planfix_user_key == "test-user-key"
        assert config.planfix_base_url == "https://test-account.planfix.ru"
        assert config.request_timeout == 30
        assert config.debug is False
    
    def test_config_with_custom_base_url(self):
        """Test config with custom base URL."""
        config = PlanfixConfig(
            planfix_account="test-account",
            planfix_api_key="test-api-key",
            planfix_user_key="test-user-key",
            planfix_base_url="https://custom.planfix.ru/"
        )
        
        assert config.planfix_base_url == "https://custom.planfix.ru"
    
    def test_config_with_optional_fields(self):
        """Test config with optional fields."""
        config = PlanfixConfig(
            planfix_account="test-account",
            planfix_api_key="test-api-key",
            planfix_user_key="test-user-key",
            request_timeout=60,
            debug=True
        )
        
        assert config.request_timeout == 60
        assert config.debug is True
    
    def test_config_missing_account(self):
        """Test config validation with missing account."""
        with pytest.raises(ValidationError) as excinfo:
            PlanfixConfig(
                planfix_api_key="test-api-key",
                planfix_user_key="test-user-key"
            )
        
        assert "planfix_account" in str(excinfo.value)
    
    def test_config_empty_account(self):
        """Test config validation with empty account."""
        with pytest.raises(ValidationError) as excinfo:
            PlanfixConfig(
                planfix_account="",
                planfix_api_key="test-api-key",
                planfix_user_key="test-user-key"
            )
        
        assert "PLANFIX_ACCOUNT" in str(excinfo.value)
    
    def test_config_missing_api_key(self):
        """Test config validation with missing API key."""
        with pytest.raises(ValidationError) as excinfo:
            PlanfixConfig(
                planfix_account="test-account",
                planfix_user_key="test-user-key"
            )
        
        assert "planfix_api_key" in str(excinfo.value)
    
    def test_config_empty_api_key(self):
        """Test config validation with empty API key."""
        with pytest.raises(ValidationError) as excinfo:
            PlanfixConfig(
                planfix_account="test-account",
                planfix_api_key="",
                planfix_user_key="test-user-key"
            )
        
        assert "PLANFIX_API_KEY" in str(excinfo.value)
    
    def test_config_missing_user_key(self):
        """Test config validation with missing user key."""
        with pytest.raises(ValidationError) as excinfo:
            PlanfixConfig(
                planfix_account="test-account",
                planfix_api_key="test-api-key"
            )
        
        assert "planfix_user_key" in str(excinfo.value)
    
    def test_config_empty_user_key(self):
        """Test config validation with empty user key."""
        with pytest.raises(ValidationError) as excinfo:
            PlanfixConfig(
                planfix_account="test-account",
                planfix_api_key="test-api-key",
                planfix_user_key=""
            )
        
        assert "PLANFIX_USER_KEY" in str(excinfo.value)
    
    def test_config_strips_whitespace(self):
        """Test that config strips whitespace from credentials."""
        config = PlanfixConfig(
            planfix_account="  test-account  ",
            planfix_api_key="  test-api-key  ",
            planfix_user_key="  test-user-key  "
        )
        
        assert config.planfix_account == "test-account"
        assert config.planfix_api_key == "test-api-key"
        assert config.planfix_user_key == "test-user-key"


class TestGetConfig:
    """Test get_config function."""
    
    @patch.dict(os.environ, {
        'PLANFIX_ACCOUNT': 'env-account',
        'PLANFIX_API_KEY': 'env-api-key',
        'PLANFIX_USER_KEY': 'env-user-key'
    })
    def test_get_config_from_env(self):
        """Test getting config from environment variables."""
        with patch('src.config.load_dotenv'):
            config = get_config()
            
            assert config.planfix_account == "env-account"
            assert config.planfix_api_key == "env-api-key"
            assert config.planfix_user_key == "env-user-key"
    
    @patch.dict(os.environ, {
        'PLANFIX_ACCOUNT': 'env-account',
        'PLANFIX_API_KEY': 'env-api-key',
        'PLANFIX_USER_KEY': 'env-user-key',
        'DEBUG': 'true',
        'REQUEST_TIMEOUT': '45'
    })
    def test_get_config_with_optional_env(self):
        """Test getting config with optional environment variables."""
        with patch('src.config.load_dotenv'):
            config = get_config()
            
            assert config.debug is True
            assert config.request_timeout == 45
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_config_missing_required_env(self):
        """Test get_config with missing required environment variables."""
        with patch('src.config.load_dotenv'):
            with pytest.raises(RuntimeError) as excinfo:
                get_config()
            
            assert "Failed to load configuration" in str(excinfo.value)
    
    @patch.dict(os.environ, {
        'PLANFIX_ACCOUNT': 'env-account',
        'PLANFIX_API_KEY': 'env-api-key',
        'PLANFIX_USER_KEY': 'env-user-key',
        'PLANFIX_BASE_URL': 'https://custom.example.com'
    })
    def test_get_config_with_custom_base_url(self):
        """Test getting config with custom base URL."""
        with patch('src.config.load_dotenv'):
            config = get_config()
            
            assert config.planfix_base_url == "https://custom.example.com"