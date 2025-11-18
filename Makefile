.PHONY: help test test-fresh test-clean test-cov test-cov-html clean-cache clean-test clean clean-docker shell

help:
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

test-cov: ## Run tests with coverage
	coverage run -m pytest

test-cov-report: ## Run tests with coverage and show console report
	coverage run -m pytest
	coverage report -m --skip-covered --sort=cover

test-cov-html: ## Run tests with coverage and generate HTML report
	coverage run -m pytest
	coverage html
	@echo "Coverage report generated in htmlcov/index.html"
	@which xdg-open > /dev/null && xdg-open htmlcov/index.html || echo "Open htmlcov/index.html in your browser"

test-reuse: ## Run tests reusing test database (fast)
	pytest --reuse-db

# Cache and cleanup targets
clean-cache: ## Remove Python cache files and directories
	@echo "Removing Python cache files..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	rm -rf docs/_build
	@echo "Removing pytest cache..."
	rm -rf .pytest_cache
	@echo "Removing mypy cache..."
	rm -rf .mypy_cache
	@echo "Removing ruff cache..."
	rm -rf .ruff_cache
	@echo "Cache cleaned!"

clean-test: ## Remove test artifacts and coverage reports
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -f coverage.xml

clean: clean-cache clean-test ## Remove all cache and test artifacts
	@echo "All clean!"

clean-docker: ## Stop containers and remove Docker images
	@echo "Stopping and removing Docker containers..."
	docker compose -f docker-compose.local.yml down --remove-orphans
	@echo "Removing Docker images..."
	docker image rm -f tasks_api_local_django 2>/dev/null || true
	docker image rm -f tasks_api_local_celeryworker 2>/dev/null || true
	docker image rm -f tasks_api_local_celerybeat 2>/dev/null || true
	docker image rm -f tasks_api_local_flower 2>/dev/null || true
	docker image rm -f tasks_api_local_docs 2>/dev/null || true
	@echo "Docker cleanup complete!"
