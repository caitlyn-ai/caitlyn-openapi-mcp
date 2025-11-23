# Multi-stage build for minimal production image
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Upgrade pip first (this rarely changes, so it's cached)
RUN pip install --no-cache-dir --upgrade "pip>=25.3" --root-user-action=ignore

# Copy pre-built wheel from CI build-package job
# The wheel is a self-contained package with all metadata
COPY dist/*.whl /tmp/

# Install the wheel (this installs only production dependencies, not dev dependencies)
# Using --no-deps would skip dependencies, but we want runtime deps installed
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir /tmp/*.whl --root-user-action=ignore

# Pre-download sentence-transformers model
# Copy only the download script to avoid invalidating this layer on source changes
ENV SENTENCE_TRANSFORMERS_HOME=/app/models
COPY scripts/download_model.py scripts/
RUN --mount=type=cache,target=/root/.cache/huggingface \
    python scripts/download_model.py

# Development stage with hot reloading support
FROM python:3.11-slim AS dev

WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade "pip>=25.3" --root-user-action=ignore

# Copy source code and dependencies for editable install
COPY pyproject.toml README.md ./
COPY src/ src/
COPY scripts/ scripts/

# Install in editable mode so volume mounts work
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -e . --root-user-action=ignore

ENV SENTENCE_TRANSFORMERS_HOME=/app/models
ENV PYTHONUNBUFFERED=1

# Copy entrypoint script
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 mcp && \
    chown -R mcp:mcp /app

USER mcp

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/caitlyn-openapi-mcp /usr/local/bin/caitlyn-openapi-mcp

# Copy pre-downloaded model cache
COPY --from=builder /app/models /app/models

# Copy entrypoint script directly (not from builder)
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 mcp && \
    chown -R mcp:mcp /app

USER mcp

# Environment variables (override these at runtime)
ENV OPENAPI_SPEC_URL="https://betty.getcaitlyn.ai/docs/openapi-v1.json"
ENV DOCS_RENDERER="scalar"
ENV DOCS_BASE_URL="https://betty.getcaitlyn.ai/api/docs"
ENV MCP_TRANSPORT="streamable-http"
ENV SENTENCE_TRANSFORMERS_HOME=/app/models

# OpenTelemetry configuration for AgentCore
# These are auto-configured by AgentCore runtime, but we set them for consistency
ENV OTEL_PYTHON_DISTRO=aws_distro
ENV OTEL_PYTHON_CONFIGURATOR=aws_configurator
ENV OTEL_TRACES_EXPORTER=otlp
ENV OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
# Set log group for AgentCore (will be overridden at runtime with actual runtime ID)
ENV OTEL_EXPORTER_OTLP_LOGS_HEADERS="x-aws-log-group=/aws/vendedlogs/bedrock-agentcore/runtime/APPLICATION_LOGS/caitlyn_mcp_openapi-63cltH8aii"
# Disable manual OTEL setup in code when running in AgentCore
ENV AGENTCORE_RUNTIME=true

# Expose port for streamable HTTP
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the server with ADOT auto-instrumentation
# The opentelemetry-instrument command is provided by aws-opentelemetry-distro package
# For local dev without ADOT, set AGENTCORE_RUNTIME=false to use manual OTEL setup
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
