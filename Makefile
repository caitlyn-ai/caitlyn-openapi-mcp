.PHONY: help install install-dev dev test test-cov lint format type-check clean build docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  make install       - Install package dependencies"
	@echo "  make install-dev   - Install package with dev dependencies"
	@echo "  make dev           - Run MCP Inspector for local development"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Run linting (ruff)"
	@echo "  make format        - Format code (black)"
	@echo "  make type-check    - Run type checking (pyright)"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make build         - Build package"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

dev:
	@echo "Starting MCP Inspector for local development..."
	npx @modelcontextprotocol/inspector \
		-e OPENAPI_SPEC_URL="https://betty.getcaitlyn.ai/docs/openapi-v1.json" \
		-e DOCS_BASE_URL="https://betty.getcaitlyn.ai/api/docs" \
		python -m openapi_mcp.server

test:
	pytest

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing

lint:
	ruff check src tests

format:
	black src tests
	ruff check --fix src tests

type-check:
	pyright

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

docker-build:
	docker build -t caitlyn-openapi-mcp .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f
