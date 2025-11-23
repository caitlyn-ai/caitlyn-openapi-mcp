#!/bin/sh
set -e

echo "Container starting..."
echo "MCP_TRANSPORT=$MCP_TRANSPORT"
echo "AGENTCORE_RUNTIME=$AGENTCORE_RUNTIME"
echo "ENABLE_TELEMETRY=$ENABLE_TELEMETRY"

# Check if we should use ADOT auto-instrumentation or manual setup
if [ "$AGENTCORE_RUNTIME" = "true" ] && command -v opentelemetry-instrument >/dev/null 2>&1; then
    echo "Using ADOT auto-instrumentation..."
    exec opentelemetry-instrument caitlyn-openapi-mcp
else
    echo "Using manual OTEL setup..."
    exec caitlyn-openapi-mcp
fi
