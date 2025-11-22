"""Tests for config module."""

import pytest

from openapi_mcp.config import AppConfig, load_config


class TestAppConfig:
    """Tests for AppConfig dataclass."""

    def test_app_config_creation(self):
        """Test AppConfig can be created with valid values."""
        config = AppConfig(
            spec_url="https://api.example.com/openapi.json",
            docs_renderer="scalar",
            docs_base_url="https://api.example.com/docs",
            transport="stdio",
        )
        assert config.spec_url == "https://api.example.com/openapi.json"
        assert config.docs_renderer == "scalar"
        assert config.docs_base_url == "https://api.example.com/docs"
        assert config.transport == "stdio"

    def test_app_config_optional_docs_base_url(self):
        """Test AppConfig with None docs_base_url."""
        config = AppConfig(
            spec_url="https://api.example.com/openapi.json",
            docs_renderer="scalar",
            docs_base_url=None,
            transport="streamable-http",
        )
        assert config.docs_base_url is None
        assert config.transport == "streamable-http"


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_with_all_env_vars(self, monkeypatch):
        """Test load_config with all environment variables set."""
        monkeypatch.setenv("OPENAPI_SPEC_URL", "https://api.example.com/openapi.json")
        monkeypatch.setenv("DOCS_RENDERER", "scalar")
        monkeypatch.setenv("DOCS_BASE_URL", "https://api.example.com/docs")
        monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")

        config = load_config()
        assert config.spec_url == "https://api.example.com/openapi.json"
        assert config.docs_renderer == "scalar"
        assert config.docs_base_url == "https://api.example.com/docs"
        assert config.transport == "streamable-http"

    def test_load_config_with_defaults(self, monkeypatch):
        """Test load_config with default values."""
        monkeypatch.setenv("OPENAPI_SPEC_URL", "https://api.example.com/openapi.json")
        # Don't set DOCS_RENDERER, DOCS_BASE_URL, or MCP_TRANSPORT

        config = load_config()
        assert config.spec_url == "https://api.example.com/openapi.json"
        assert config.docs_renderer == "scalar"  # default
        assert config.docs_base_url is None
        assert config.transport == "stdio"  # default

    def test_load_config_missing_spec_url(self, monkeypatch):
        """Test load_config raises error when OPENAPI_SPEC_URL is missing."""
        # Ensure OPENAPI_SPEC_URL is not set
        monkeypatch.delenv("OPENAPI_SPEC_URL", raising=False)

        with pytest.raises(RuntimeError, match="OPENAPI_SPEC_URL is required"):
            load_config()

    def test_load_config_renderer_case_insensitive(self, monkeypatch):
        """Test DOCS_RENDERER is converted to lowercase."""
        monkeypatch.setenv("OPENAPI_SPEC_URL", "https://api.example.com/openapi.json")
        monkeypatch.setenv("DOCS_RENDERER", "SCALAR")

        config = load_config()
        assert config.docs_renderer == "scalar"

    def test_load_config_transport_stdio(self, monkeypatch):
        """Test MCP_TRANSPORT with stdio value."""
        monkeypatch.setenv("OPENAPI_SPEC_URL", "https://api.example.com/openapi.json")
        monkeypatch.setenv("MCP_TRANSPORT", "stdio")

        config = load_config()
        assert config.transport == "stdio"

    def test_load_config_transport_streamable_http(self, monkeypatch):
        """Test MCP_TRANSPORT with streamable-http value."""
        monkeypatch.setenv("OPENAPI_SPEC_URL", "https://api.example.com/openapi.json")
        monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")

        config = load_config()
        assert config.transport == "streamable-http"

    def test_load_config_transport_case_insensitive(self, monkeypatch):
        """Test MCP_TRANSPORT is converted to lowercase."""
        monkeypatch.setenv("OPENAPI_SPEC_URL", "https://api.example.com/openapi.json")
        monkeypatch.setenv("MCP_TRANSPORT", "STDIO")

        config = load_config()
        assert config.transport == "stdio"

    def test_load_config_invalid_transport(self, monkeypatch):
        """Test load_config raises error for invalid transport."""
        monkeypatch.setenv("OPENAPI_SPEC_URL", "https://api.example.com/openapi.json")
        monkeypatch.setenv("MCP_TRANSPORT", "invalid-transport")

        with pytest.raises(RuntimeError, match="Invalid MCP_TRANSPORT"):
            load_config()
