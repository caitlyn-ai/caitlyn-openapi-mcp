# OpenTelemetry Integration

This MCP server includes comprehensive OpenTelemetry (OTEL) instrumentation for traces and logs.

## Quick Start

### Local Development with OTEL Collector

The easiest way to use telemetry during development is to run `make dev`, which automatically starts:
1. **OTEL Collector** - Receives and processes telemetry data
2. **Jaeger** - Provides a UI to visualize traces
3. **MCP Server** - Sends telemetry to the collector

```bash
# Start everything (OTEL collector + Jaeger + MCP server)
# This automatically opens Jaeger UI in your browser
make dev
```

When you're done:
```bash
# Stop everything (MCP server + OTEL collector + Jaeger)
make dev-stop
```

### Standalone OTEL Collector

You can also run the OTEL collector independently:

```bash
# Start OTEL collector and Jaeger
make otel-up

# View collector logs
make otel-logs

# Stop OTEL collector
make otel-down
```

## Architecture

```
┌─────────────────┐
│   MCP Server    │  Sends traces + logs via OTLP
│  (Python app)   │  ───────────────────┐
└─────────────────┘                      │
                                         ▼
                              ┌──────────────────┐
                              │ OTEL Collector   │
                              │ localhost:4317   │
                              └──────────────────┘
                                   │         │
                      ┌────────────┘         └──────────┐
                      ▼                                  ▼
          ┌──────────────────┐                ┌──────────────────┐
          │     Jaeger       │                │  traces.json     │
          │  localhost:16686 │                │ (local file)     │
          └──────────────────┘                └──────────────────┘
```

## What Gets Instrumented

### Traces (Spans)

The server creates detailed spans for:

#### OpenAPI Spec Loading
- `openapi.load_spec_full` - Complete spec loading operation
  - `openapi.check_cache` - Cache lookup (cache_hit attribute)
  - `openapi.fetch_and_parse` - HTTP fetch + parsing (spec_size_bytes)
  - `openapi.save_cache` - Cache write
  - `openapi.create_spec_object` - Spec object creation
  - `openapi.extract_endpoints` - Endpoint extraction (endpoint_count)
  - `openapi.extract_schemas` - Schema extraction (schema_count)

#### Vector Search
- `vector_search.init` - Vector index initialization
  - `vector_search.load_model` - Load sentence-transformers model
  - `vector_search.create_texts` - Generate searchable texts
  - `vector_search.load_or_generate` - Load/generate embeddings
    - `vector_search.load_cache` - Load from cache
    - `vector_search.generate_embeddings` - Generate new embeddings
    - `vector_search.save_cache` - Save to cache
- `vector_search.search` - Search operation
  - `vector_search.encode_query` - Encode search query
  - `vector_search.compute_similarity` - Calculate similarities (max_similarity, avg_similarity)
  - `vector_search.rank_results` - Rank and filter results

#### MCP Protocol
- `mcp.server.create` - Server initialization
- `mcp.list_tools` - Tool listing (mcp.first_request)
- `mcp.list_resources` - Resource listing
- `mcp.call_tool` - Tool execution (protocol-level)

#### MCP Tool Execution
- `mcp.tool.list_api_endpoints` - List endpoints with optional tag/search filters
  - Attributes: tag, search, result_count
- `mcp.tool.get_endpoint_details` - Get specific endpoint details
  - Attributes: method, path, found (boolean)
- `mcp.tool.get_schema_definition` - Get schema structure
  - Attributes: schema_name, found (boolean)
- `mcp.tool.search_api_endpoints` - Semantic/keyword search for endpoints
  - Attributes: query, max_results, search_method (vector/substring), result_count
- `mcp.tool.list_api_tags` - List all API tags/categories
  - Attributes: tag_count

### Logs

All Python `logging` output is captured as OTEL log records and sent to the collector alongside traces. This includes:
- INFO logs (startup messages, cache hits)
- WARNING logs (fallback behaviors, cache misses)
- ERROR logs (failures, exceptions)

## Configuration

### Environment Variables

```bash
# OTLP Endpoint (default: http://localhost:4317)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Service name (default: caitlyn-openapi-mcp)
OTEL_SERVICE_NAME=caitlyn-openapi-mcp

# Enable/disable telemetry (default: true)
ENABLE_TELEMETRY=true

# File export path (default: ./mcp-spans.json)
OTEL_FILE_EXPORT=./mcp-spans.json
```

### OTEL Collector Configuration

The collector is configured in [`otel-collector-config.yaml`](../otel-collector-config.yaml):

- **Receivers**: OTLP gRPC (4317) and HTTP (4318)
- **Processors**:
  - Batch processing for performance
  - Resource attributes injection
  - Memory limiting (512MB limit, 128MB spike)
- **Exporters**:
  - Jaeger (for visualization)
  - File (for debugging)
  - Logging (for development)

## Viewing Telemetry

### Jaeger UI

Open http://localhost:16686 and:

1. **Select Service**: Choose "caitlyn-openapi-mcp"
2. **Find Traces**: Click "Find Traces"
3. **View Details**: Click on a trace to see the span waterfall

You'll see:
- Request timing (which operations are slow)
- Cache hit/miss patterns
- Vector search performance
- Error traces with full context

### File Export

Traces are also exported to `otel-data/traces.json` for debugging:

```bash
# View raw trace data
cat otel-data/traces.json | python -m json.tool
```

### Local Span Export (Debugging)

For quick debugging without the collector, spans are also written to `mcp-spans.json`:

```bash
# View simplified span data
cat mcp-spans.json | python -m json.tool
```

## Testing Telemetry

Run the test script to verify telemetry is working:

```bash
# Start OTEL collector first
make otel-up

# Run telemetry test
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 python scripts/test_telemetry.py

# Check Jaeger UI for "test-telemetry" service
open http://localhost:16686
```

## Production Deployment

For production, you can:

1. **Use a managed OTEL service** (e.g., Honeycomb, Datadog, New Relic):
   ```bash
   OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io:443
   OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=YOUR_API_KEY"
   ```

2. **Run your own collector cluster**:
   ```bash
   OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-collector.your-domain.com:4317
   ```

3. **Disable telemetry**:
   ```bash
   ENABLE_TELEMETRY=false
   ```

## Troubleshooting

### No traces appearing in Jaeger

1. Check OTEL collector is running:
   ```bash
   docker compose -f docker-compose.otel.yml ps
   ```

2. Check collector logs:
   ```bash
   make otel-logs
   ```

3. Verify MCP server is sending to collector:
   ```bash
   # Should show OTLP endpoint configuration
   cat mcp-spans.json
   ```

### Collector connection refused

Ensure the collector is running before starting the MCP server:
```bash
make otel-up
# Wait for "Everything is ready" message
make dev
```

### Missing spans

Spans are batched for performance. Wait a few seconds after operations complete, then check Jaeger UI again.

## Performance Impact

Telemetry has minimal overhead:
- Span creation: ~0.01ms per span
- Batch processing: async, non-blocking
- Network export: batched every 5 seconds

The overhead is typically <1% of total request time.
