from __future__ import annotations

import logging
import threading
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .config import load_config
from .docs_links import attach_docs_links
from .model import OpenApiIndex
from .openapi_loader import load_openapi_spec_from_url
from .resources import register_resources
from .telemetry import setup_telemetry
from .tools import register_tools

logger = logging.getLogger(__name__)


class IndexLoader:
    """Manages background loading of OpenAPI index."""

    def __init__(self):
        self._index: Optional[OpenApiIndex] = None
        self._lock = threading.Lock()
        self._loading = False
        self._loaded = False
        self._load_thread: Optional[threading.Thread] = None

    def start_loading_background(self, spec_url: str, docs_renderer: str, docs_base_url: str | None) -> None:
        """Start loading the index in a background thread."""
        with self._lock:
            if self._loading or self._loaded:
                return
            self._loading = True

        def _load():
            try:
                logger.info("Starting background OpenAPI spec load...")
                cfg = load_config()
                index = load_openapi_spec_from_url(cfg.spec_url)
                attach_docs_links(index, renderer=cfg.docs_renderer, base_url=cfg.docs_base_url)

                # Start vector index loading (also in background)
                index.start_loading_vector_index_background()

                with self._lock:
                    self._index = index
                    self._loaded = True
                    self._loading = False
                logger.info("✓ OpenAPI spec loaded and ready")
            except Exception as e:
                logger.error(f"Failed to load OpenAPI spec: {e}")
                with self._lock:
                    self._loading = False
                raise

        self._load_thread = threading.Thread(target=_load, daemon=True, name="openapi-spec-loader")
        self._load_thread.start()

    def get_index(self) -> OpenApiIndex:
        """Get the loaded index, waiting if necessary."""
        # If not loaded yet, wait for the background thread
        if not self._loaded and self._load_thread:
            logger.info("Waiting for OpenAPI spec to finish loading...")
            self._load_thread.join()

        with self._lock:
            if self._index is None:
                raise RuntimeError("OpenAPI index failed to load")
            return self._index


# Global index loader
_index_loader = IndexLoader()


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
    cfg = load_config()
    mcp = FastMCP(name="caitlyn-openapi-mcp")

    # Start loading OpenAPI spec in background (non-blocking)
    _index_loader.start_loading_background(
        spec_url=cfg.spec_url,
        docs_renderer=cfg.docs_renderer,
        docs_base_url=cfg.docs_base_url,
    )
    logger.info("✓ Server starting (loading spec in background)...")

    # Register resources and tools - they will wait for index when called
    register_resources(mcp, index_loader=_index_loader)
    register_tools(mcp, index_loader=_index_loader)

    return mcp


def main() -> None:
    """
    Main entry point for the MCP server.

    Transport mode is configured via MCP_TRANSPORT environment variable:
    - "stdio" (default): For local development and Claude Desktop
    - "streamable-http": For Bedrock AgentCore deployment
    """
    # Configure logging to stderr (stdout is used for MCP JSON-RPC protocol)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=__import__("sys").stderr,
    )

    # Initialize OpenTelemetry
    setup_telemetry()

    cfg = load_config()
    mcp = create_server()
    mcp.run(transport=cfg.transport)


if __name__ == "__main__":
    main()
