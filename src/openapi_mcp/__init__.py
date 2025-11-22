"""Caitlyn OpenAPI MCP Server.

MCP server that exposes OpenAPI specifications as queryable documentation resources
for LLMs, with Scalar deep links.
"""

from .config import AppConfig, load_config
from .docs_links import attach_docs_links
from .model import Endpoint, OpenApiIndex
from .openapi_loader import load_openapi_spec_from_url
from .server import create_server, main

__version__ = "0.3.0"

__all__ = [
    "AppConfig",
    "Endpoint",
    "OpenApiIndex",
    "attach_docs_links",
    "create_server",
    "load_config",
    "load_openapi_spec_from_url",
    "main",
]
