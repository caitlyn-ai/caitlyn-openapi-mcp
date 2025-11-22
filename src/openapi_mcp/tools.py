from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from .server import IndexLoaderProtocol


def register_tools(mcp: FastMCP, *, index_loader: IndexLoaderProtocol) -> None:
    """
    Register MCP tools for exploring and understanding the API.

    These tools help LLMs answer user questions like:
    - "What can this API do?"
    - "How do I create a resource?"
    - "What parameters does endpoint X need?"

    Args:
        mcp: FastMCP server instance
        index_loader: Index loader that provides access to the parsed OpenAPI index
    """
    from .telemetry import trace_operation

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
        with trace_operation("mcp.tool.list_api_endpoints", {"tag": tag, "search": search}) as span:
            index = index_loader.get_index()
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

            if span:
                span.set_attribute("result_count", len(results))

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
        with trace_operation("mcp.tool.get_endpoint_details", {"method": method, "path": path}) as span:
            index = index_loader.get_index()
            method_upper = method.upper()
            for ep in index.endpoints:
                if ep.method == method_upper and ep.path == path:
                    if span:
                        span.set_attribute("found", True)
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
            if span:
                span.set_attribute("found", False)
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
        with trace_operation("mcp.tool.get_schema_definition", {"schema_name": schema_name}) as span:
            index = index_loader.get_index()
            schema = index.schemas.get(schema_name)
            if schema is None:
                if span:
                    span.set_attribute("found", False)
                return None
            if span:
                span.set_attribute("found", True)
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
        with trace_operation("mcp.tool.search_api_endpoints", {"query": query, "max_results": max_results}) as span:
            index = index_loader.get_index()
            # Try vector search first if available
            # Lazy initialization happens here on first search
            index.ensure_vector_index()

            if index.vector_index is not None:
                if span:
                    span.set_attribute("search_method", "vector")
                vector_results = index.vector_index.search(query, top_k=max_results)
                results = [
                    {
                        "path": ep.path,
                        "method": ep.method,
                        "summary": ep.summary or "",
                        "description": ep.description or "",
                        "operation_id": ep.operation_id or "",
                        "tags": ep.tags,
                        "docs_url": ep.docs_url,
                        "relevance_score": round(score, 3),
                    }
                    for ep, score in vector_results
                ]
                if span:
                    span.set_attribute("result_count", len(results))
                return results

            # Fallback to substring search if vector search unavailable
            if span:
                span.set_attribute("search_method", "substring")
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

            if span:
                span.set_attribute("result_count", len(matches))
            return matches

    @mcp.tool()
    def list_api_tags() -> list[dict[str, Any]]:
        """
        Get all API categories/tags to understand how the API is organized. Use this to discover what functional areas the API covers.

        Returns:
            List of tags with endpoint counts
        """
        with trace_operation("mcp.tool.list_api_tags", {}) as span:
            index = index_loader.get_index()
            tag_counts: dict[str, int] = {}

            for ep in index.endpoints:
                for tag in ep.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

            results = [{"tag": tag, "endpoint_count": count} for tag, count in sorted(tag_counts.items())]
            if span:
                span.set_attribute("tag_count", len(results))
            return results
