#!/bin/sh
set -e

echo "Container starting..."
echo "MCP_TRANSPORT=$MCP_TRANSPORT"
echo "AGENTCORE_RUNTIME=$AGENTCORE_RUNTIME"

# Run with OpenTelemetry instrumentation
exec opentelemetry-instrument caitlyn-openapi-mcp
