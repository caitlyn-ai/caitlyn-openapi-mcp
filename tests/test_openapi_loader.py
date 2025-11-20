"""Tests for openapi_loader module."""

import pytest
from unittest.mock import MagicMock, patch

from openapi_mcp.openapi_loader import load_openapi_spec_from_url


@pytest.fixture
def minimal_openapi_spec():
    """Minimal valid OpenAPI 3.0 spec."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "summary": "List users",
                    "description": "Get a list of all users",
                    "operationId": "listUsers",
                    "tags": ["users"],
                    "parameters": [],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/UserList"}
                                }
                            },
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                    },
                },
                "UserList": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/User"},
                },
            },
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
            },
        },
    }


@pytest.mark.unit
class TestLoadOpenApiSpec:
    """Tests for load_openapi_spec_from_url function."""

    @patch("openapi_mcp.openapi_loader.ResolvingParser")
    def test_load_spec_from_url(self, mock_parser_class, minimal_openapi_spec):
        """Test loading OpenAPI spec from URL."""
        # Setup mock
        mock_parser = MagicMock()
        mock_parser.specification = minimal_openapi_spec
        mock_parser_class.return_value = mock_parser

        # Load spec
        spec_url = "https://api.example.com/openapi.json"
        index = load_openapi_spec_from_url(spec_url)

        # Verify parser was called with correct URL and backend
        mock_parser_class.assert_called_once_with(spec_url, backend="openapi-spec-validator")

        # Verify index structure
        assert index.spec_url == spec_url
        assert index.raw == minimal_openapi_spec
        assert len(index.endpoints) == 1
        assert len(index.schemas) == 2
        assert "User" in index.schemas
        assert "UserList" in index.schemas
        assert len(index.security_schemes) == 1
        assert "bearerAuth" in index.security_schemes

    @patch("openapi_mcp.openapi_loader.ResolvingParser")
    def test_endpoint_extraction(self, mock_parser_class, minimal_openapi_spec):
        """Test that endpoints are correctly extracted."""
        mock_parser = MagicMock()
        mock_parser.specification = minimal_openapi_spec
        mock_parser_class.return_value = mock_parser

        index = load_openapi_spec_from_url("https://api.example.com/openapi.json")

        # Check endpoint details
        endpoint = index.endpoints[0]
        assert endpoint.path == "/users"
        assert endpoint.method == "GET"
        assert endpoint.summary == "List users"
        assert endpoint.description == "Get a list of all users"
        assert endpoint.operation_id == "listUsers"
        assert endpoint.tags == ["users"]
        assert endpoint.docs_url is None  # Not set by loader

    @patch("openapi_mcp.openapi_loader.ResolvingParser")
    def test_empty_components(self, mock_parser_class):
        """Test handling of spec with no components."""
        spec_without_components = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }

        mock_parser = MagicMock()
        mock_parser.specification = spec_without_components
        mock_parser_class.return_value = mock_parser

        index = load_openapi_spec_from_url("https://api.example.com/openapi.json")

        assert index.schemas == {}
        assert index.security_schemes == {}
        assert index.endpoints == []

    @patch("openapi_mcp.openapi_loader.ResolvingParser")
    def test_multiple_methods(self, mock_parser_class):
        """Test endpoint extraction with multiple HTTP methods."""
        spec_multi_methods = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "operationId": "listUsers",
                        "responses": {"200": {"description": "Success"}},
                    },
                    "post": {
                        "summary": "Create user",
                        "operationId": "createUser",
                        "responses": {"201": {"description": "Created"}},
                    },
                }
            },
        }

        mock_parser = MagicMock()
        mock_parser.specification = spec_multi_methods
        mock_parser_class.return_value = mock_parser

        index = load_openapi_spec_from_url("https://api.example.com/openapi.json")

        assert len(index.endpoints) == 2
        methods = {ep.method for ep in index.endpoints}
        assert methods == {"GET", "POST"}
