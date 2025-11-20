from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .config import load_config
from .docs_links import attach_docs_links
from .openapi_loader import load_openapi_spec_from_url
from .resources import register_resources
from .tools import register_tools


def build_index():
    """
    Build the OpenAPI index by loading the spec from URL and attaching docs links.

    Returns:
        OpenApiIndex with all endpoints, schemas, and security schemes indexed
    """
    cfg = load_config()
    index = load_openapi_spec_from_url(cfg.spec_url)
    attach_docs_links(index, renderer=cfg.docs_renderer, base_url=cfg.docs_base_url)
    return index


def create_server() -> FastMCP:
    """
    Create and configure the MCP server.

    Returns:
        Configured FastMCP server instance
    """
    mcp = FastMCP(name="caitlyn-openapi-mcp")
    index = build_index()

    register_resources(mcp, index=index)
    register_tools(mcp, index=index)

    return mcp


def main() -> None:
    """
    Main entry point for the MCP server.

    Transport mode is configured via MCP_TRANSPORT environment variable:
    - "stdio" (default): For local development and Claude Desktop
    - "streamable-http": For Bedrock AgentCore deployment
    """
    cfg = load_config()
    mcp = create_server()
    mcp.run(transport=cfg.transport)


if __name__ == "__main__":
    main()
