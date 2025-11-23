.PHONY: help install install-dev setup-models dev dev-http dev-stop otel-up otel-down otel-logs test test-cov lint format type-check clean clean-models build docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  make install       - Install package dependencies"
	@echo "  make install-dev   - Install package with dev dependencies"
	@echo "  make setup-models  - Download sentence-transformers model to local cache"
	@echo "  make dev           - Run MCP Inspector with OTEL collector for local development (stdio)"
	@echo "  make dev-http      - Run MCP server with hot reload + Jaeger (port 8000)"
	@echo "  make dev-stop      - Stop dev server"
	@echo "  make otel-up       - Start OTEL collector and Jaeger"
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
	@echo "  make docker-build  - Build Docker image (production)"
	@echo "  make docker-build-dev - Build Docker image (development with hot reload)"
	@echo "  make docker-run    - Run Docker container (production)"
	@echo "  make docker-dev    - Run Docker container in dev mode with hot reloading"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	@$(MAKE) setup-models

setup-models:
	@if [ -d "models/models--sentence-transformers--all-MiniLM-L6-v2" ]; then \
		echo "✓ Model already cached in ./models/"; \
	else \
		echo "Downloading sentence-transformers model to ./models/..."; \
		mkdir -p models; \
		SENTENCE_TRANSFORMERS_HOME=./models python scripts/download_model.py; \
	fi

otel-up:
	@echo "Starting OTEL Collector and Jaeger..."
	@mkdir -p otel-data
	docker compose -f docker-compose.dev.yml up -d otel-collector jaeger
	@echo "✓ OTEL Collector: localhost:4317"
	@echo "✓ Jaeger UI: http://localhost:16686"

otel-down:
	@echo "Stopping OTEL services..."
	docker compose -f docker-compose.dev.yml down
	@echo "✓ Stopped"

otel-logs:
	docker compose -f docker-compose.dev.yml logs -f

dev:
	@echo "Starting OTEL Collector and Jaeger..."
	@$(MAKE) otel-up
	@sleep 2
	@echo ""
	@echo "Starting MCP Inspector..."
	@(sleep 5 && open http://localhost:16686 2>/dev/null || true) &
	npx @modelcontextprotocol/inspector \
		-e OPENAPI_SPEC_URL="https://betty.getcaitlyn.ai/docs/openapi-v1.json" \
		-e DOCS_BASE_URL="https://betty.getcaitlyn.ai/api/docs" \
		-e SENTENCE_TRANSFORMERS_HOME="$(shell pwd)/models" \
		-e OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317" \
		-e OTEL_EXPORTER_OTLP_PROTOCOL="grpc" \
		-e ENABLE_TELEMETRY="true" \
		-- python -m openapi_mcp.server

dev-http:
	@echo "Starting dev environment..."
	@$(MAKE) docker-build-dev
	@$(MAKE) setup-models
	@docker compose -f docker-compose.dev.yml down 2>/dev/null || true
	@docker compose -f docker-compose.dev.yml up -d
	@sleep 3
	@echo ""
	@echo "✓ MCP Server: http://localhost:8000/mcp"
	@echo "✓ Jaeger UI: http://localhost:16686"
	@echo ""
	@(sleep 3 && open http://localhost:16686 2>/dev/null || true) &
	npx @modelcontextprotocol/inspector

dev-stop:
	@pkill -f "@modelcontextprotocol/inspector" 2>/dev/null || true
	@docker compose -f docker-compose.dev.yml down
	@echo "✓ Stopped"

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

docker-build: build
	docker build -t caitlyn-openapi-mcp .

docker-build-dev:
	docker build --target dev -t caitlyn-openapi-mcp:dev .

docker-run:
	docker compose up -d

docker-dev:
	@$(MAKE) docker-build-dev
	@$(MAKE) setup-models
	docker compose up openapi-mcp-dev

docker-stop:
	docker compose down

docker-logs:
	docker compose logs -f
