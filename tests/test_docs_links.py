"""Tests for docs_links module."""

import pytest
from openapi_core import Spec

from openapi_mcp.docs_links import attach_docs_links
from openapi_mcp.model import Endpoint, OpenApiIndex


@pytest.fixture
def sample_endpoint():
    """Create a sample endpoint for testing."""
    return Endpoint(
        path="/api/v1/users",
        method="GET",
        summary="List users",
        description="Get a list of all users",
        operation_id="listUsers",
        tags=["users"],
        parameters=[],
        request_body=None,
        responses={},
        docs_url=None,
    )


@pytest.fixture
def sample_index(sample_endpoint):
    """Create a sample OpenApiIndex for testing."""
    minimal_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
    }
    spec = Spec.from_dict(minimal_spec)  # type: ignore[arg-type]

    return OpenApiIndex(
        spec=spec,
        raw=minimal_spec,
        endpoints=[sample_endpoint],
        schemas={"User": {"type": "object", "properties": {}}},
        security_schemes={"bearerAuth": {"type": "http", "scheme": "bearer"}},
        spec_url="https://api.example.com/openapi.json",
        schema_docs_urls={},
        security_scheme_docs_urls={},
    )


class TestAttachDocsLinks:
    """Tests for attach_docs_links function."""

    def test_attach_scalar_links(self, sample_index):
        """Test attaching Scalar documentation links."""
        base_url = "https://api.example.com/docs"
        attach_docs_links(sample_index, renderer="scalar", base_url=base_url)

        # Check endpoint docs_url (includes api_prefix from spec title "Test API" + version "1.0.0" -> "test-api-v1")
        endpoint = sample_index.endpoints[0]
        assert endpoint.docs_url == "https://api.example.com/docs#test-api-v1/tag/users/get/api/v1/users"

        # Check schema docs_urls (includes api_prefix)
        assert "User" in sample_index.schema_docs_urls
        assert sample_index.schema_docs_urls["User"] == "https://api.example.com/docs#test-api-v1/schema/User"

        # Check security scheme docs_urls (includes api_prefix)
        assert "bearerAuth" in sample_index.security_scheme_docs_urls
        assert sample_index.security_scheme_docs_urls["bearerAuth"] == "https://api.example.com/docs#test-api-v1/security/bearerAuth"

    def test_attach_links_no_base_url(self, sample_index):
        """Test that no links are attached when base_url is None."""
        attach_docs_links(sample_index, renderer="scalar", base_url=None)

        # Check that docs_url remains None
        endpoint = sample_index.endpoints[0]
        assert endpoint.docs_url is None
        assert sample_index.schema_docs_urls == {}
        assert sample_index.security_scheme_docs_urls == {}

    def test_endpoint_without_tags(self, sample_index):
        """Test endpoint link generation when endpoint has no tags."""
        endpoint = sample_index.endpoints[0]
        endpoint.tags = []

        base_url = "https://api.example.com/docs"
        attach_docs_links(sample_index, renderer="scalar", base_url=base_url)

        # Should use "default" tag (includes api_prefix)
        assert endpoint.docs_url == "https://api.example.com/docs#test-api-v1/tag/default/get/api/v1/users"

    def test_endpoint_with_special_characters(self, sample_index):
        """Test endpoint link generation with special characters in path."""
        endpoint = sample_index.endpoints[0]
        endpoint.path = "/api/v1/users/{userId}/posts"

        base_url = "https://api.example.com/docs"
        attach_docs_links(sample_index, renderer="scalar", base_url=base_url)

        # Should preserve {} and / but encode other characters (includes api_prefix)
        assert endpoint.docs_url == "https://api.example.com/docs#test-api-v1/tag/users/get/api/v1/users/{userId}/posts"

    def test_post_method(self, sample_index):
        """Test endpoint link generation for POST method."""
        endpoint = sample_index.endpoints[0]
        endpoint.method = "POST"

        base_url = "https://api.example.com/docs"
        attach_docs_links(sample_index, renderer="scalar", base_url=base_url)

        assert endpoint.docs_url == "https://api.example.com/docs#test-api-v1/tag/users/post/api/v1/users"

    def test_schema_with_special_characters(self, sample_index):
        """Test schema link generation with special characters in name."""
        sample_index.schemas["User-Profile"] = {"type": "object"}

        base_url = "https://api.example.com/docs"
        attach_docs_links(sample_index, renderer="scalar", base_url=base_url)

        # Should preserve - but encode other special characters (includes api_prefix)
        assert "User-Profile" in sample_index.schema_docs_urls
        assert sample_index.schema_docs_urls["User-Profile"] == "https://api.example.com/docs#test-api-v1/schema/User-Profile"
