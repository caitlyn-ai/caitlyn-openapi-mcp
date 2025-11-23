# Multi-stage build for minimal production image
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first (this rarely changes, so it's cached)
RUN pip install --no-cache-dir --upgrade "pip>=25.3"

# Copy only pyproject.toml for dependency installation
# Don't copy README.md here - documentation changes shouldn't invalidate dependency cache
COPY pyproject.toml .

# Install dependencies only (without source code)
# This layer will be cached unless dependencies in pyproject.toml change
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir build && \
    pip wheel --no-cache-dir --wheel-dir=/app/wheels . && \
    pip install --no-cache-dir --find-links=/app/wheels --no-index caitlyn-openapi-mcp || \
    pip install --no-cache-dir .

# Pre-download sentence-transformers model BEFORE copying source code
# This ensures model cache persists even when source code changes
# Copy only the download script needed for this step
ENV SENTENCE_TRANSFORMERS_HOME=/app/models
COPY scripts/download_model.py scripts/
RUN --mount=type=cache,target=/root/.cache/huggingface \
    python scripts/download_model.py

# Now copy remaining source code (this changes frequently but won't invalidate model or dependency cache)
COPY README.md .
COPY src/ src/
COPY scripts/ scripts/

# Reinstall to include source code
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --force-reinstall --no-deps .

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/caitlyn-openapi-mcp /usr/local/bin/caitlyn-openapi-mcp

# Copy pre-downloaded model cache
COPY --from=builder /app/models /app/models

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
CMD ["sh", "-c", "echo 'Container starting...' && echo 'MCP_TRANSPORT='$MCP_TRANSPORT && echo 'AGENTCORE_RUNTIME='$AGENTCORE_RUNTIME && opentelemetry-instrument caitlyn-openapi-mcp"]
