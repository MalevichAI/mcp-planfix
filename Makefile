# Makefile for Planfix MCP Server

.PHONY: help install install-dev test test-coverage lint format check clean run dev docs build

# Default target
help: ## Show this help message
	@echo "Planfix MCP Server - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install production dependencies
	uv sync --no-dev

install-dev: ## Install development dependencies
	uv sync

# Testing
test: ## Run tests
	uv run pytest tests/ -v

test-coverage: ## Run tests with coverage report
	uv run pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

test-api: ## Test API connection
	uv run python -c "import asyncio; from src.planfix_api import PlanfixAPI; asyncio.run(PlanfixAPI().test_connection())"

# Code quality
lint: ## Run linting checks
	uv run ruff check src/ tests/
	uv run mypy src/

format: ## Format code
	uv run ruff format src/ tests/

check: ## Run all quality checks
	@echo "🔍 Running code quality checks..."
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/
	uv run mypy src/
	@echo "✅ All checks passed!"

fix: ## Fix code issues automatically
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

# Development
run: ## Run the MCP server
	uv run python src/planfix_server.py

dev: ## Run server in development mode with MCP inspector
	uv run mcp dev src/planfix_server.py

debug: ## Run server with debug logging
	DEBUG=true uv run python src/planfix_server.py

# Examples
examples: ## Run basic usage examples
	uv run python examples/basic_usage.py

examples-advanced: ## Run advanced workflow examples
	uv run python examples/advanced_workflows.py

# Claude Desktop integration
install-claude: ## Install server in Claude Desktop
	uv run mcp install src/planfix_server.py --name "Planfix Integration" -f .env

uninstall-claude: ## Remove server from Claude Desktop
	@echo "Manually remove 'planfix' section from claude_desktop_config.json"

# Documentation
docs: ## Generate documentation
	@echo "📚 Documentation is available in docs/ directory"
	@echo "  - docs/api_reference.md - API Reference"
	@echo "  - docs/troubleshooting.md - Troubleshooting Guide"

# Maintenance
clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

clean-all: clean ## Clean everything including uv cache
	uv cache clean

# Environment
env-check: ## Check environment variables
	@echo "🔍 Checking environment variables..."
	@echo "PLANFIX_ACCOUNT: $(if $(PLANFIX_ACCOUNT),✅ Set,❌ Missing)"
	@echo "PLANFIX_API_KEY: $(if $(PLANFIX_API_KEY),✅ Set,❌ Missing)"
	@echo "PLANFIX_USER_KEY: $(if $(PLANFIX_USER_KEY),✅ Set,❌ Missing)"
	@echo ""
	@if [ -z "$(PLANFIX_ACCOUNT)" ] || [ -z "$(PLANFIX_API_KEY)" ] || [ -z "$(PLANFIX_USER_KEY)" ]; then \
		echo "❌ Missing required environment variables!"; \
		echo "   Please check your .env file or set the variables manually."; \
		exit 1; \
	else \
		echo "✅ All required environment variables are set!"; \
	fi

env-example: ## Create example .env file
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📝 Created .env file from template"; \
		echo "   Please edit .env with your actual Planfix credentials"; \
	else \
		echo "⚠️  .env file already exists"; \
	fi

# Build and distribution
build: ## Build package
	uv build

publish-test: build ## Publish to test PyPI
	uv publish --repository testpypi

publish: build ## Publish to PyPI
	uv publish

# Quick start
setup: install-dev env-example ## Quick setup for development
	@echo "🚀 Development environment setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env file with your Planfix credentials"
	@echo "  2. Run 'make test-api' to verify connection"
	@echo "  3. Run 'make dev' to start development server"
	@echo "  4. Run 'make install-claude' to integrate with Claude Desktop"

# CI/CD helpers
ci-test: ## Run tests in CI environment
	uv run pytest tests/ --cov=src --cov-report=xml --junitxml=test-results.xml

ci-check: ## Run all CI checks
	uv run ruff check src/ tests/ --output-format=github
	uv run mypy src/ --junit-xml=mypy-results.xml

# Database/API operations
reset-cache: ## Clear any API caches (if implemented)
	@echo "🗑️  Clearing caches..."
	# Add cache clearing commands here if needed

health-check: ## Run health check
	@echo "🏥 Running health check..."
	uv run python -c "
import asyncio
import sys
from src.config import get_config
from src.planfix_api import PlanfixAPI

async def health_check():
    try:
        config = get_config()
        print(f'✅ Configuration loaded: {config.planfix_account}')
        
        api = PlanfixAPI()
        connection_ok = await api.test_connection()
        
        if connection_ok:
            print('✅ Planfix API connection successful')
            
            tasks = await api.search_tasks(status='active')
            print(f'✅ API functionality test: found {len(tasks)} active tasks')
            
            print('🎉 Health check passed!')
            return True
        else:
            print('❌ Planfix API connection failed')
            return False
            
    except Exception as e:
        print(f'❌ Health check failed: {e}')
        return False

success = asyncio.run(health_check())
sys.exit(0 if success else 1)
"

# Performance testing
perf-test: ## Run basic performance tests
	@echo "⚡ Running performance tests..."
	uv run python -c "
import asyncio
import time
from src.planfix_api import PlanfixAPI

async def perf_test():
    api = PlanfixAPI()
    
    # Test search performance
    start = time.time()
    tasks = await api.search_tasks(status='active', limit=10)
    search_time = time.time() - start
    
    print(f'📊 Search 10 active tasks: {search_time:.2f}s')
    
    if tasks:
        # Test get task performance
        start = time.time()
        task = await api.get_task(tasks[0].id)
        get_time = time.time() - start
        print(f'📊 Get task details: {get_time:.2f}s')
    
    print('⚡ Performance test completed')

asyncio.run(perf_test())
"