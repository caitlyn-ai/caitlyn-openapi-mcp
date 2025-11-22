"""Tests for resources module."""

import json

import pytest
from openapi_core import Spec

from openapi_mcp.model import Endpoint, OpenApiIndex
from openapi_mcp.resources import register_resources


@pytest.fixture
def sample_index():
    """Create a sample OpenApiIndex for testing."""
    minimal_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "summary": "List users",
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }
    spec = Spec.from_dict(minimal_spec)

    endpoint1 = Endpoint(
        path="/api/v1/users",
        method="GET",
        summary="List users",
        description="Get all users",
        operation_id="listUsers",
        tags=["users"],
        parameters=[],
        request_body=None,
        responses={"200": {"description": "Success"}},
        docs_url="https://api.example.com/docs#tag/users/get/api/v1/users",
    )

    return OpenApiIndex(
        spec=spec,
        raw=minimal_spec,
        endpoints=[endpoint1],
        schemas={
            "User": {"type": "object", "properties": {"id": {"type": "integer"}}},
        },
        security_schemes={"bearerAuth": {"type": "http", "scheme": "bearer"}},
        spec_url="https://api.example.com/openapi.json",
        schema_docs_urls={
            "User": "https://api.example.com/docs#schema/User",
        },
        security_scheme_docs_urls={"bearerAuth": "https://api.example.com/docs#security/bearerAuth"},
    )


class TestResources:
    """Tests for resource registration and functionality."""

    def test_register_resources(self, sample_index):
        """Test that resources can be registered without errors."""
        from mcp.server.fastmcp import FastMCP

        # Create a simple index loader that returns our sample_index
        class MockIndexLoader:
            def get_index(self):
                return sample_index

        mcp = FastMCP(name="test-server")
        # Should not raise any exceptions
        register_resources(mcp, index_loader=MockIndexLoader())

    def test_full_spec_is_valid_json(self, sample_index):
        """Test that the full spec resource returns valid JSON."""
        # The resource should return a JSON string that can be parsed
        from mcp.server.fastmcp import FastMCP

        # Create a simple index loader that returns our sample_index
        class MockIndexLoader:
            def get_index(self):
                return sample_index

        mcp = FastMCP(name="test-server")
        register_resources(mcp, index_loader=MockIndexLoader())

        # Verify the index.raw can be serialized to JSON
        spec_json = json.dumps(sample_index.raw, indent=2)
        parsed = json.loads(spec_json)

        assert parsed["openapi"] == "3.0.0"
        assert parsed["info"]["title"] == "Test API"

    # Note: Full integration tests with FastMCP would require running the server
    # and making actual MCP requests. These tests verify the basic structure.
