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

### Using pip (from PyPI)

Once published, install from PyPI:

```bash
pip install caitlyn-openapi-mcp
```

### Using uvx (recommended)

For isolated execution without global installation:

```bash
uvx caitlyn-openapi-mcp
```

### From source

```bash
git clone https://github.com/caitlyn-ai/caitlyn-openapi-mcp.git
cd caitlyn-openapi-mcp
pip install -e .
```

### Development installation

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

## MCP Client Setup

This server can be used with any MCP-compatible client. Below are configuration examples for popular clients.

### Claude Desktop (stdio transport)

Claude Desktop uses stdio transport by default - no need to set `MCP_TRANSPORT`.

Add this configuration to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

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

**Using uvx** (recommended for isolated environments):

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

The server automatically uses stdio transport for Claude Desktop communication.

### Cline (VS Code Extension)

Add to your MCP settings in VS Code:

**File**: `.vscode/mcp.json` or global settings

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

### AWS Bedrock AgentCore (streamable-http transport)

For Bedrock AgentCore deployment, set `MCP_TRANSPORT=streamable-http`:

#### Docker Deployment

```dockerfile
# Dockerfile with Bedrock configuration
FROM your-base-image

ENV OPENAPI_SPEC_URL=https://api.example.com/openapi.json
ENV DOCS_BASE_URL=https://api.example.com/docs
ENV MCP_TRANSPORT=streamable-http

CMD ["caitlyn-openapi-mcp"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  openapi-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAPI_SPEC_URL=https://api.example.com/openapi.json
      - DOCS_BASE_URL=https://api.example.com/docs
      - MCP_TRANSPORT=streamable-http
```

#### Programmatic Usage

```python
import os
from openapi_mcp.server import create_server

# Set transport mode for Bedrock
os.environ["MCP_TRANSPORT"] = "streamable-http"
os.environ["OPENAPI_SPEC_URL"] = "https://api.example.com/openapi.json"
os.environ["DOCS_BASE_URL"] = "https://api.example.com/docs"

mcp = create_server()
mcp.run()  # Uses streamable-http from env
```

Deploy as a containerized service and configure your Bedrock agent to connect to the HTTP endpoint.

### Generic MCP Client Configuration

For any MCP client that supports command-based servers:

```json
{
  "command": "/path/to/python",
  "args": ["-m", "openapi_mcp.server"],
  "env": {
    "OPENAPI_SPEC_URL": "https://your-api.com/openapi.json",
    "DOCS_RENDERER": "scalar",
    "DOCS_BASE_URL": "https://your-api.com/docs"
  }
}
```

### Example: Caitlyn API

Configure for the Caitlyn API with Scalar documentation:

```json
{
  "mcpServers": {
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

### Multiple API Configurations

You can configure multiple OpenAPI specs by running separate server instances:

```json
{
  "mcpServers": {
    "api-production": {
      "command": "uvx",
      "args": ["caitlyn-openapi-mcp"],
      "env": {
        "OPENAPI_SPEC_URL": "https://api.prod.example.com/openapi.json",
        "DOCS_BASE_URL": "https://docs.prod.example.com"
      }
    },
    "api-staging": {
      "command": "uvx",
      "args": ["caitlyn-openapi-mcp"],
      "env": {
        "OPENAPI_SPEC_URL": "https://api.staging.example.com/openapi.json",
        "DOCS_BASE_URL": "https://docs.staging.example.com"
      }
    }
  }
}
```

### Troubleshooting Client Setup

**Issue**: Server fails to start in Claude Desktop

**Solutions**:
- Verify Python is in your PATH: `which python` (macOS/Linux) or `where python` (Windows)
- Use full path to Python: `"/usr/local/bin/python3.11"`
- Check Claude Desktop logs: `~/Library/Logs/Claude/mcp*.log` (macOS)
- Ensure `OPENAPI_SPEC_URL` is accessible from your machine

**Issue**: "ModuleNotFoundError: No module named 'openapi_mcp'"

**Solutions**:
- Install the package: `pip install caitlyn-openapi-mcp`
- Or use uvx for automatic installation: `uvx caitlyn-openapi-mcp`
- Verify installation: `python -m openapi_mcp.server --help`

**Issue**: Tools not appearing in Claude Desktop

**Solutions**:
- Restart Claude Desktop completely
- Check the server is running: Look for the process in Activity Monitor/Task Manager
- Verify configuration JSON is valid (use a JSON validator)
- Check server logs for errors

## Usage

### Running the server

```bash
# Set required environment variables
export OPENAPI_SPEC_URL="https://api.example.com/openapi.json"
export DOCS_BASE_URL="https://api.example.com/docs"

# Run the server
caitlyn-openapi-mcp
```

### Using Docker

```bash
docker build -t caitlyn-openapi-mcp .

docker run -p 8000:8000 \
  -e OPENAPI_SPEC_URL="https://api.example.com/openapi.json" \
  -e DOCS_BASE_URL="https://api.example.com/docs" \
  caitlyn-openapi-mcp
```

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

## Development

### Running tests

```bash
pytest
```

### Code formatting

```bash
black src tests
ruff check src tests
```

### Type checking

```bash
pyright
```

### Running with coverage

```bash
pytest --cov=src --cov-report=html
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

[Your license here]

## Contributing

[Your contributing guidelines here]
