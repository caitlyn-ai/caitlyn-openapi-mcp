"""Tests for tools module."""

import pytest
from openapi_core import Spec

from openapi_mcp.model import Endpoint, OpenApiIndex
from openapi_mcp.tools import register_tools


@pytest.fixture
def sample_index():
    """Create a sample OpenApiIndex for testing."""
    minimal_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
    }
    spec = Spec.from_dict(minimal_spec)  # type: ignore[arg-type]

    endpoint1 = Endpoint(
        path="/api/v1/users",
        method="GET",
        summary="List users",
        description="Get all users from the system",
        operation_id="listUsers",
        tags=["users"],
        parameters=[{"name": "limit", "in": "query", "schema": {"type": "integer"}}],
        request_body=None,
        responses={"200": {"description": "Success"}},
        docs_url="https://api.example.com/docs#tag/users/get/api/v1/users",
    )

    endpoint2 = Endpoint(
        path="/api/v1/posts",
        method="POST",
        summary="Create post",
        description="Create a new blog post",
        operation_id="createPost",
        tags=["posts"],
        parameters=[],
        request_body={"content": {"application/json": {}}},
        responses={"201": {"description": "Created"}},
        docs_url="https://api.example.com/docs#tag/posts/post/api/v1/posts",
    )

    endpoint3 = Endpoint(
        path="/api/v1/users/{userId}",
        method="GET",
        summary="Get user",
        description="Get a specific user by ID",
        operation_id="getUser",
        tags=["users"],
        parameters=[{"name": "userId", "in": "path", "required": True, "schema": {"type": "string"}}],
        request_body=None,
        responses={"200": {"description": "Success"}},
        docs_url="https://api.example.com/docs#tag/users/get/api/v1/users/{userId}",
    )

    return OpenApiIndex(
        spec=spec,
        raw=minimal_spec,
        endpoints=[endpoint1, endpoint2, endpoint3],
        schemas={
            "User": {"type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}}},
            "Post": {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}}},
        },
        security_schemes={"bearerAuth": {"type": "http", "scheme": "bearer"}},
        spec_url="https://api.example.com/openapi.json",
        schema_docs_urls={
            "User": "https://api.example.com/docs#schema/User",
            "Post": "https://api.example.com/docs#schema/Post",
        },
        security_scheme_docs_urls={"bearerAuth": "https://api.example.com/docs#security/bearerAuth"},
    )


class TestTools:
    """Tests for tool registration and functionality."""

    def test_register_tools(self, sample_index):
        """Test that tools can be registered without errors."""
        from mcp.server.fastmcp import FastMCP

        # Create a simple index loader that returns our sample_index
        class MockIndexLoader:
            def get_index(self):
                return sample_index

        mcp = FastMCP(name="test-server")
        # Should not raise any exceptions
        register_tools(mcp, index_loader=MockIndexLoader())

    # Note: Full integration tests with FastMCP would require running the server
    # and making actual MCP tool calls. These tests verify the basic structure.
    # The tool logic is tested implicitly through the endpoint/schema filtering behavior.
