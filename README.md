# Caitlyn OpenAPI MCP Server

MCP server that exposes OpenAPI specifications as queryable documentation resources for LLMs, with Scalar deep links.

## Features

- **URL-based OpenAPI spec loading**: Load specs from any URL, not just local files
- **$ref resolution**: Automatically resolves all `$ref` references (including remote refs) using Prance
- **Semantic search**: Vector-based endpoint search using sentence-transformers for better query understanding
- **Scalar deep links**: Every endpoint, schema, and security scheme includes a `docs_url` pointing to Scalar documentation
- **MCP resources**: Expose spec structure for introspection
- **MCP tools**: Search and query endpoints, schemas, and security schemes
- **Streamable HTTP**: Built for Bedrock AgentCore integration

## Installation

### Using uvx (recommended)

For isolated execution without global installation:

```bash
uvx caitlyn-openapi-mcp
```

### Using pip

Install from PyPI:

```bash
pip install caitlyn-openapi-mcp
```

### From source

For local development or testing:

```bash
git clone https://github.com/caitlyn-ai/caitlyn-openapi-mcp.git
cd caitlyn-openapi-mcp
pip install -e ".[dev]"
```

## Configuration

The server is configured via environment variables:

### Required

- `OPENAPI_SPEC_URL`: Full URL to the OpenAPI JSON/YAML specification
  - Example: `https://api.example.com/openapi.json`
  - Example: `https://raw.githubusercontent.com/org/repo/main/openapi.yaml`

### Optional

- `DOCS_RENDERER`: Documentation renderer type (default: `"scalar"`)

  - Currently only `"scalar"` is supported

- `DOCS_BASE_URL`: Base URL of the Scalar documentation UI

  - Example: `https://api.example.com/docs`
  - Example: `https://api.example.com/scalar`
  - If not provided, `docs_url` fields will be `null`

- `MCP_TRANSPORT`: Transport mode (default: `"stdio"`)
  - `"stdio"`: For local development and Claude Desktop (default)
  - `"streamable-http"`: For AWS Bedrock AgentCore deployment

### OpenTelemetry (Optional)

For observability in production environments:

**General OTEL Configuration:**
- `ENABLE_TELEMETRY`: Enable/disable telemetry (default: `"true"`)
- `OTEL_SERVICE_NAME`: Service name for tracing (default: `"caitlyn-openapi-mcp"`)
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OTLP endpoint for traces (e.g., `"http://localhost:4317"`)

**AWS Bedrock AgentCore (ADOT):**

The Docker image includes AWS Distro for OpenTelemetry (ADOT) for native AgentCore integration. When deployed to AgentCore, traces are automatically exported to CloudWatch.

Pre-configured environment variables (already set in Dockerfile):
- `OTEL_PYTHON_DISTRO=aws_distro`
- `OTEL_PYTHON_CONFIGURATOR=aws_configurator`
- `OTEL_TRACES_EXPORTER=otlp`
- `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf`

Additional variables for non-AgentCore hosted deployment:
- `AWS_DEFAULT_REGION`, `AWS_REGION`: AWS region
- `AWS_ACCOUNT_ID`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: AWS credentials
- `AGENT_OBSERVABILITY_ENABLED=true`: Enable AgentCore observability

**Instrumented operations:**
- OpenAPI spec loading
- Vector search index initialization (model loading, embedding generation, cache operations)
- Semantic search queries (with result counts)

## Client Configuration

### 1. Claude Desktop with uvx (Recommended)

The easiest way to use this server with Claude Desktop. No installation required - uvx automatically downloads and runs the package.

**Config file location:**

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "openapi-docs": {
      "command": "uvx",
      "args": ["caitlyn-openapi-mcp"],
      "env": {
        "OPENAPI_SPEC_URL": "https://api.example.com/openapi.json",
        "DOCS_BASE_URL": "https://api.example.com/docs"
      }
    }
  }
}
```

### 2. Claude Desktop with Local Development

For testing local changes to the server code.

**Prerequisites**: Clone the repo and install in development mode (see [Local Development](#local-development))

```json
{
  "mcpServers": {
    "openapi-docs": {
      "command": "python",
      "args": ["-m", "openapi_mcp.server"],
      "env": {
        "OPENAPI_SPEC_URL": "https://api.example.com/openapi.json",
        "DOCS_BASE_URL": "https://api.example.com/docs"
      }
    }
  }
}
```

**Note**: Use the full path to Python if it's not in your PATH: `"/usr/local/bin/python3.11"`

### 3. MCP Inspector for Local Development

For interactive testing with a web UI before deploying to Claude Desktop.

**Prerequisites**:

- Clone and install in development mode (see [Local Development](#local-development))
- Node.js installed (npx comes with Node.js)

**Quick start:**

```bash
make dev
```

**Or manually set your own API:**

```bash
npx @modelcontextprotocol/inspector \
  -e OPENAPI_SPEC_URL="https://api.example.com/openapi.json" \
  -e DOCS_BASE_URL="https://api.example.com/docs" \
  python -m openapi_mcp.server
```

See [Testing with MCP Inspector](#testing-with-mcp-inspector) for more details.

### 4. AWS Bedrock AgentCore

Deploy as a containerized service with streamable-http transport and AWS Distro for OpenTelemetry (ADOT) for native observability.

**Features:**
- 🚀 **Fast cold-starts** - Embedding cache for ~10x faster initialization
- 📊 **ADOT integration** - Native CloudWatch tracing via `opentelemetry-instrument`
- 🔒 **Secure** - Non-root user, multi-stage builds, updated pip (CVE-2025-8869 fixed)
- 📦 **Production-ready** - Pre-bundled model cache, health checks

**Quick start:**

1. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your OPENAPI_SPEC_URL and AWS credentials
   ```

2. Run with docker-compose:
   ```bash
   docker-compose up openapi-mcp-bedrock
   ```

**See full examples:**
- [Dockerfile](Dockerfile) - Multi-stage build with ADOT auto-instrumentation
- [docker-compose.yml](docker-compose.yml) - Complete service definitions
- [.env.example](.env.example) - All configuration options

**Build and run:**

```bash
docker build -t openapi-mcp .
docker run -p 8000:8000 openapi-mcp
```

Configure your Bedrock agent to connect to the HTTP endpoint.

### 5. Multiple APIs with Claude Desktop

Connect to multiple OpenAPI specifications simultaneously by running separate server instances.

```json
{
  "mcpServers": {
    "production-api": {
      "command": "uvx",
      "args": ["caitlyn-openapi-mcp"],
      "env": {
        "OPENAPI_SPEC_URL": "https://api.prod.example.com/openapi.json",
        "DOCS_BASE_URL": "https://docs.prod.example.com"
      }
    },
    "staging-api": {
      "command": "uvx",
      "args": ["caitlyn-openapi-mcp"],
      "env": {
        "OPENAPI_SPEC_URL": "https://api.staging.example.com/openapi.json",
        "DOCS_BASE_URL": "https://docs.staging.example.com"
      }
    },
    "caitlyn-api": {
      "command": "uvx",
      "args": ["caitlyn-openapi-mcp"],
      "env": {
        "OPENAPI_SPEC_URL": "https://betty.getcaitlyn.ai/docs/openapi-v1.json",
        "DOCS_BASE_URL": "https://betty.getcaitlyn.ai/api/docs"
      }
    }
  }
}
```

Each server runs independently with its own OpenAPI specification.

## Troubleshooting

### Server fails to start in Claude Desktop

- Verify Python is in your PATH: `which python` (macOS/Linux) or `where python` (Windows)
- Use full path to Python: `"/usr/local/bin/python3.11"`
- Check Claude Desktop logs: `~/Library/Logs/Claude/mcp*.log` (macOS)
- Ensure `OPENAPI_SPEC_URL` is accessible from your machine

### "ModuleNotFoundError: No module named 'openapi_mcp'"

- For uvx: This shouldn't happen - uvx installs automatically
- For local Python: Run `pip install caitlyn-openapi-mcp` or `pip install -e ".[dev]"` in the repo
- Verify installation: `python -m openapi_mcp.server --help`

### Tools not appearing in Claude Desktop

- Restart Claude Desktop completely (quit and reopen)
- Verify your JSON configuration is valid (use a JSON validator)
- Check the server is running in Activity Monitor (macOS) or Task Manager (Windows)
- Check Claude Desktop logs for errors

### OpenAPI spec fails to load

- Verify the URL is accessible: `curl https://your-api.com/openapi.json`
- Check server logs for detailed error messages
- Ensure the spec is valid OpenAPI 3.x format
- If the spec has broken `$ref` references, the server will load it anyway with warnings

## MCP Resources

The server exposes one static resource:

### `api-specification`

The complete OpenAPI 3.x specification in JSON format (fully resolved with all $refs expanded). Can be used with OpenAPI validation tools, code generators, or for reference.

## MCP Tools

The server provides tools designed to help LLMs answer user questions about the API. Each tool includes contextual descriptions to guide when it should be used.

### `list_api_endpoints`

**Use for:** Getting an overview of what the API can do, or finding endpoints by category.

**Parameters:**

- `tag` (optional): Filter by API category/tag (e.g., "users", "posts", "auth")
- `search` (optional): Search term to find endpoints (searches paths, descriptions, summaries)

**Returns:** List of endpoints with path, method, summary, description, tags, and docs_url

**Example use cases:**

- User asks: "What can this API do?"
- User asks: "Show me all user-related endpoints"

### `get_endpoint_details`

**Use for:** Getting detailed information about a specific endpoint including parameters, request body, and responses.

**Parameters:**

- `method`: HTTP method (GET, POST, PUT, DELETE, PATCH, etc.)
- `path`: API path (e.g., "/api/v1/users" or "/users/{userId}")

**Returns:** Complete endpoint details including parameters, request body schema, response schemas, and docs_url

**Example use cases:**

- User asks: "How do I call the create user endpoint?"
- User asks: "What parameters does the GET /users endpoint need?"
- User asks: "What's the request body for creating a post?"

### `get_schema_definition`

**Use for:** Understanding the structure of request/response data models.

**Parameters:**

- `schema_name`: Name of the schema (e.g., "User", "CreateUserRequest", "PaginatedResponse")

**Returns:** Schema definition with properties, types, required fields, and docs_url

**Example use cases:**

- User asks: "What fields does a User object have?"
- User asks: "What's the structure of the CreatePostRequest?"
- User asks: "What does the response look like?"

### `search_api_endpoints`

**Use for:** Finding endpoints by functionality when you don't know the exact path.

**Parameters:**

- `query`: What the user wants to do (e.g., "create knowledge base", "upload file", "get user profile")
- `max_results` (optional, default: 20): Maximum number of results to return

**Returns:** Matching endpoints with path, method, summary, description, tags, and docs_url

**Example use cases:**

- User asks: "How do I create a knowledge base through the API?"
- User asks: "Can I upload files?"
- User asks: "Is there an endpoint for user authentication?"

### `list_api_tags`

**Use for:** Understanding how the API is organized into functional categories.

**Parameters:** None

**Returns:** List of tags/categories with endpoint counts

**Example use cases:**

- User asks: "What functional areas does this API cover?"
- User asks: "How is this API organized?"

## Scalar Deep Links

When `DOCS_BASE_URL` is configured, the server generates deep links to Scalar documentation:

### Endpoint links

Format: `{base_url}#tag/{tag}/{method}/{path}`

Example: `https://api.example.com/docs#tag/users/get/api/v1/users`

- `tag`: The first tag on the operation (defaults to "default" if no tags)
- `method`: HTTP method in lowercase (get, post, etc.)
- `path`: OpenAPI path with leading slash stripped

### Schema links

Format: `{base_url}#schema/{schemaName}`

Example: `https://api.example.com/docs#schema/User`

### Security scheme links

Format: `{base_url}#security/{schemeName}`

Example: `https://api.example.com/docs#security/bearerAuth`

## Local Development

### Setup

Clone the repository and install in development mode:

```bash
git clone https://github.com/caitlyn-ai/caitlyn-openapi-mcp.git
cd caitlyn-openapi-mcp
pip install -e ".[dev]"
```

The installation automatically downloads the sentence-transformers model (~80MB) to `./models/` for semantic search.

**Startup behavior:**

- **Server starts instantly** (~100-200ms) - No blocking on spec or model loading
- **Background loading**: OpenAPI spec and ML model load in parallel background threads
- **First request handling**:
  - If spec/model still loading, request waits for completion
  - Typically completes before first request (spec: ~1-2s cached, model: ~1-2s cached)
- **Semantic search ready in ~1-2 seconds** (cached) or ~5-10 seconds (first time)
  - **Spec cache**: Resolved OpenAPI spec cached to disk (~instant subsequent loads)
  - **Embedding cache**: Pre-computed embeddings cached per-API-spec (~instant loads)
  - **First load of new API**: Downloads spec + generates embeddings (~5-10s)
  - **Subsequent loads**: Loads from cache (~1-2s total) ✨ **~5-10x faster**

**Caching strategy:**

- **OpenAPI specs**: Cached in `./models/cache/spec_*.pkl` (per-URL hash, gitignored)
- **Model files**: Cached in `./models/` directory (gitignored)
- **Embeddings**: Cached in `./models/cache/embeddings_*.pkl` (per-content hash, gitignored)
- **First-time setup**: ~30 seconds to download model + fetch spec + generate embeddings
- **Cold-start (cached)**: ~1-2 seconds to load everything from cache 🚀
- **Cache invalidation**: Automatic when API spec content or URL changes
- **Manual management**:
  - Download/update model: `make setup-models`
  - Clear all caches: `make clean-models`

**Note:** Docker builds pre-download the model during image build, so containers start instantly with model already cached in memory.

### Testing with MCP Inspector

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) provides a web-based UI for testing your MCP server locally.

**Prerequisites**: Node.js installed (npx comes with Node.js)

**Quick start with Make:**

```bash
make dev
```

This launches the inspector with the Caitlyn API. The inspector will open a web interface where you can:

- Test all MCP tools interactively
- View resources and their contents
- Inspect endpoint details, schemas, and security schemes
- Validate the server behavior before deployment

**Manual usage with custom API:**

```bash
npx @modelcontextprotocol/inspector \
  -e OPENAPI_SPEC_URL="https://api.example.com/openapi.json" \
  -e DOCS_BASE_URL="https://api.example.com/docs" \
  python -m openapi_mcp.server
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test files
pytest tests/test_openapi_loader.py
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
pyright

# Run all checks
black src tests && ruff check src tests && pyright && pytest
```

## Architecture

The server is built with the following components:

- **config.py**: Environment-based configuration
- **model.py**: Data models for endpoints, schemas, and the OpenAPI index
- **openapi_loader.py**: URL-based OpenAPI spec loading using Prance and openapi-core
- **docs_links.py**: Documentation deep link generation (currently Scalar only)
- **resources.py**: MCP resource definitions
- **tools.py**: MCP tool definitions
- **server.py**: Main server wiring and entry point

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

For security issues, please refer to our [Security Policy](SECURITY.md).
