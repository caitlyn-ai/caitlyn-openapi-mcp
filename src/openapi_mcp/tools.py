from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .model import OpenApiIndex


def register_tools(mcp: FastMCP, *, index: OpenApiIndex) -> None:
    """
    Register MCP tools for exploring and understanding the API.

    These tools help LLMs answer user questions like:
    - "What can this API do?"
    - "How do I create a resource?"
    - "What parameters does endpoint X need?"

    Args:
        mcp: FastMCP server instance
        index: Parsed OpenAPI index with documentation links
    """

    @mcp.tool()
    def list_api_endpoints(
        tag: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get an overview of available API endpoints. Use this to answer "What can this API do?" or to find endpoints by category.

        Args:
            tag: Filter by API category/tag (e.g., "users", "posts", "auth")
            search: Search term to find endpoints (searches paths, descriptions, summaries)

        Returns:
            List of endpoints with path, method, summary, description, tags, and docs_url
        """
        results: list[dict[str, Any]] = []
        needle = search.lower() if search else None

        for ep in index.endpoints:
            # Filter by tag if specified
            if tag and tag not in ep.tags:
                continue

            # Filter by search term if specified
            if needle:
                haystack = " ".join(
                    [
                        ep.path,
                        ep.method,
                        ep.summary or "",
                        ep.description or "",
                        ep.operation_id or "",
                        " ".join(ep.tags),
                    ]
                ).lower()
                if needle not in haystack:
                    continue

            results.append(
                {
                    "path": ep.path,
                    "method": ep.method,
                    "summary": ep.summary,
                    "description": ep.description,
                    "operation_id": ep.operation_id,
                    "tags": ep.tags,
                    "docs_url": ep.docs_url,
                }
            )

        return results

    @mcp.tool()
    def get_endpoint_details(method: str, path: str) -> dict | None:
        """
        Get detailed information about a specific endpoint. Use this to answer "How do I call endpoint X?" or "What parameters does endpoint Y need?"

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH, etc.)
            path: API path (e.g., "/api/v1/users" or "/users/{userId}")

        Returns:
            Complete endpoint details including parameters, request body schema, response schemas, and docs_url, or None if not found
        """
        method_upper = method.upper()
        for ep in index.endpoints:
            if ep.method == method_upper and ep.path == path:
                return {
                    "path": ep.path,
                    "method": ep.method,
                    "summary": ep.summary,
                    "description": ep.description,
                    "operation_id": ep.operation_id,
                    "tags": ep.tags,
                    "parameters": ep.parameters,
                    "request_body": ep.request_body,
                    "responses": ep.responses,
                    "docs_url": ep.docs_url,
                }
        return None

    @mcp.tool()
    def get_schema_definition(schema_name: str) -> dict | None:
        """
        Get the structure of a data schema. Use this to answer "What fields does a User object have?" or "What's the structure of the request/response?"

        Args:
            schema_name: Name of the schema (e.g., "User", "CreateUserRequest", "PaginatedResponse")

        Returns:
            Schema definition with properties, types, required fields, and docs_url, or None if not found
        """
        schema = index.schemas.get(schema_name)
        if schema is None:
            return None
        return {
            "name": schema_name,
            "schema": schema,
            "docs_url": index.schema_docs_urls.get(schema_name),
        }

    @mcp.tool()
    def search_api_endpoints(query: str, max_results: int = 20) -> list[dict[str, Any]]:
        """
        Search for endpoints by functionality. Use this when the user asks about capabilities like "How do I create a knowledge base?" or "Can I upload files?"

        Args:
            query: What the user wants to do (e.g., "create knowledge base", "upload file", "get user profile")
            max_results: Maximum number of results to return (default: 20)

        Returns:
            Matching endpoints with path, method, summary, description, and docs_url
        """
        needle = query.lower()
        matches: list[dict[str, Any]] = []

        for ep in index.endpoints:
            haystack = " ".join(
                [
                    ep.path,
                    ep.method,
                    ep.summary or "",
                    ep.description or "",
                    ep.operation_id or "",
                    " ".join(ep.tags),
                ]
            ).lower()

            if needle in haystack:
                matches.append(
                    {
                        "path": ep.path,
                        "method": ep.method,
                        "summary": ep.summary or "",
                        "description": ep.description or "",
                        "operation_id": ep.operation_id or "",
                        "tags": ep.tags,
                        "docs_url": ep.docs_url,
                    }
                )
                if len(matches) >= max_results:
                    break

        return matches

    @mcp.tool()
    def list_api_tags() -> list[dict[str, Any]]:
        """
        Get all API categories/tags to understand how the API is organized. Use this to discover what functional areas the API covers.

        Returns:
            List of tags with endpoint counts
        """
        tag_counts: dict[str, int] = {}

        for ep in index.endpoints:
            for tag in ep.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return [{"tag": tag, "endpoint_count": count} for tag, count in sorted(tag_counts.items())]
