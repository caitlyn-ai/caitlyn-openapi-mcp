# Caitlyn OpenAPI MCP Server

MCP server that exposes OpenAPI specifications as queryable documentation resources for LLMs, with Scalar deep links.

## Features

- **URL-based OpenAPI spec loading**: Load specs from any URL, not just local files
- **$ref resolution**: Automatically resolves all `$ref` references (including remote refs) using Prance
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

Deploy as a containerized service with streamable-http transport.

**docker-compose.yml:**

```yaml
version: "3.8"

services:
  openapi-mcp:
    image: python:3.11-slim
    working_dir: /app
    command: sh -c "pip install caitlyn-openapi-mcp && caitlyn-openapi-mcp"
    ports:
      - "8000:8000"
    environment:
      - OPENAPI_SPEC_URL=https://api.example.com/openapi.json
      - DOCS_BASE_URL=https://api.example.com/docs
      - MCP_TRANSPORT=streamable-http
```

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir caitlyn-openapi-mcp

ENV OPENAPI_SPEC_URL=https://api.example.com/openapi.json
ENV DOCS_BASE_URL=https://api.example.com/docs
ENV MCP_TRANSPORT=streamable-http

CMD ["caitlyn-openapi-mcp"]
```

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
