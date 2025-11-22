from __future__ import annotations

from typing import TYPE_CHECKING

from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from .server import IndexLoaderProtocol


def register_resources(mcp: FastMCP, *, index_loader: IndexLoaderProtocol) -> None:
    """
    Register MCP resources for the OpenAPI specification.

    Resources provide static reference content. For querying and exploring the API,
    use the tools instead (list_api_endpoints, get_endpoint_details, etc.).

    Args:
        mcp: FastMCP server instance
        index_loader: Index loader that provides access to the parsed OpenAPI index
    """

    @mcp.resource("openapi://api-specification")
    def get_full_api_spec() -> str:
        """
        The complete OpenAPI 3.x specification in JSON format.
        This is the raw, fully-resolved spec (all $refs expanded).
        Can be used with OpenAPI validation tools, code generators, etc.
        """
        import json

        index = index_loader.get_index()
        return json.dumps(index.raw, indent=2)
