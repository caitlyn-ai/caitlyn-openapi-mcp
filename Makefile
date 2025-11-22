.PHONY: help install install-dev setup-models dev dev-stop otel-up otel-down otel-logs test test-cov lint format type-check clean clean-models build docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  make install       - Install package dependencies"
	@echo "  make install-dev   - Install package with dev dependencies"
	@echo "  make setup-models  - Download sentence-transformers model to local cache"
	@echo "  make dev           - Run MCP Inspector with OTEL collector for local development"
	@echo "  make dev-stop      - Stop MCP Inspector and OTEL collector"
	@echo "  make otel-up       - Start OTEL collector and Jaeger (standalone)"
	@echo "  make otel-down     - Stop OTEL collector and Jaeger"
	@echo "  make otel-logs     - Show OTEL collector logs"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Run linting (ruff)"
	@echo "  make format        - Format code (black)"
	@echo "  make type-check    - Run type checking (pyright)"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make clean-models  - Remove cached sentence-transformers models"
	@echo "  make build         - Build package"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	@$(MAKE) setup-models

setup-models:
	@echo "Downloading sentence-transformers model to ./models/..."
	@mkdir -p models
	@SENTENCE_TRANSFORMERS_HOME=./models python scripts/download_model.py

otel-up:
	@echo "Starting OTEL Collector and Jaeger..."
	@mkdir -p otel-data
	docker compose -f docker-compose.otel.yml up -d
	@echo "✓ OTEL Collector running on localhost:4317 (gRPC) and localhost:4318 (HTTP)"
	@echo "✓ Jaeger UI available at http://localhost:16686"

otel-down:
	@echo "Stopping OTEL Collector and Jaeger..."
	docker compose -f docker-compose.otel.yml down
	@echo "✓ OTEL services stopped"

otel-logs:
	docker compose -f docker-compose.otel.yml logs -f

dev:
	@echo "Starting OTEL Collector and Jaeger..."
	@$(MAKE) otel-up
	@echo ""
	@echo "Starting MCP Inspector for local development..."
	npx @modelcontextprotocol/inspector \
		-e OPENAPI_SPEC_URL="https://betty.getcaitlyn.ai/docs/openapi-v1.json" \
		-e DOCS_BASE_URL="https://betty.getcaitlyn.ai/api/docs" \
		-e SENTENCE_TRANSFORMERS_HOME="$(shell pwd)/models" \
		-e OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317" \
		-e ENABLE_TELEMETRY="true" \
		-- python -m openapi_mcp.server

dev-stop:
	@echo "Stopping MCP Inspector and server..."
	@pkill -f "@modelcontextprotocol/inspector" 2>/dev/null || true
	@pkill -f "python.*openapi_mcp.server" 2>/dev/null || true
	@echo "✓ Stopped MCP Inspector processes"
	@echo ""
	@$(MAKE) otel-down

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

clean-models:
	@echo "Removing cached sentence-transformers models..."
	rm -rf models/

build: clean
	python -m build

docker-build:
	docker build -t caitlyn-openapi-mcp .

docker-run:
	docker compose up -d

docker-stop:
	docker compose down

docker-logs:
	docker compose logs -f
