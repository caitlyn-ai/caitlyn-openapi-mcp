# Quick Start Guide

Get up and running with Caitlyn OpenAPI MCP in minutes!

## Prerequisites

- Python 3.11 or higher
- pip
- Docker (optional, for containerized deployment)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/caitlyn-ai/caitlyn-openapi-mcp.git
cd caitlyn-openapi-mcp
```

### 2. Install dependencies

```bash
# Install package with dependencies
make install

# Or install manually
pip install -e .
```

### 3. Configure environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set your OpenAPI spec URL
export OPENAPI_SPEC_URL="https://api.example.com/openapi.json"
export DOCS_BASE_URL="https://api.example.com/docs"
```

### 4. Run the server

```bash
# Run directly
caitlyn-openapi-mcp

# Or using Python module
python -m openapi_mcp.server
```

## Docker Quick Start

### 1. Build the image

```bash
make docker-build
```

### 2. Configure environment

Edit `.env` file with your configuration:

```bash
OPENAPI_SPEC_URL=https://api.example.com/openapi.json
DOCS_RENDERER=scalar
DOCS_BASE_URL=https://api.example.com/docs
```

### 3. Run with docker-compose

```bash
make docker-run
```

### 4. View logs

```bash
make docker-logs
```

### 5. Stop the server

```bash
make docker-stop
```

## Testing Your Setup

### Run tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov
```

### Example OpenAPI Specs

You can test with these public OpenAPI specifications:

1. **Caitlyn API**
   ```bash
   export OPENAPI_SPEC_URL="https://betty.getcaitlyn.ai/docs/openapi-v1.json"
   export DOCS_BASE_URL="https://betty.getcaitlyn.ai/api/docs"
   ```

2. **PetStore API** (OpenAPI example)
   ```bash
   export OPENAPI_SPEC_URL="https://petstore3.swagger.io/api/v3/openapi.json"
   export DOCS_BASE_URL="https://petstore3.swagger.io"
   ```

## Verify Installation

Check that the server is working:

```bash
# The server should start without errors
# You should see MCP server initialization messages
```

## Next Steps

- Read the [README.md](README.md) for detailed documentation
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Explore the MCP resources and tools available

## Common Issues

### Issue: `OPENAPI_SPEC_URL is required` error

**Solution**: Make sure you've set the `OPENAPI_SPEC_URL` environment variable:

```bash
export OPENAPI_SPEC_URL="https://your-api.com/openapi.json"
```

### Issue: Cannot resolve $refs

**Solution**: Ensure your OpenAPI spec URL is accessible and all remote $refs can be resolved. Prance will automatically handle this if the URLs are valid.

### Issue: Docker container fails to start

**Solution**: Check your `.env` file is properly configured and the OpenAPI spec URL is accessible from within the container.

## Getting Help

- Open an issue on GitHub
- Check the [README.md](README.md) for detailed documentation
- Review the [CONTRIBUTING.md](CONTRIBUTING.md) for development setup
