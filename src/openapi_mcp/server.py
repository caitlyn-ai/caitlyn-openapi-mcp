from __future__ import annotations

import logging
import threading

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
        self._index: OpenApiIndex | None = None
        self._lock = threading.Lock()
        self._loading = False
        self._loaded = False
        self._load_thread: threading.Thread | None = None

    def start_loading_background(self, spec_url: str, docs_renderer: str, docs_base_url: str | None) -> None:
        """Start loading the index in a background thread."""
        with self._lock:
            if self._loading or self._loaded:
                return
            self._loading = True

        def _load():
            from .telemetry import trace_operation

            try:
                with trace_operation("openapi.background_load", {"spec_url": spec_url}):
                    logger.info("Starting background OpenAPI spec load...")
                    cfg = load_config()
                    index = load_openapi_spec_from_url(cfg.spec_url)

                    with trace_operation("openapi.attach_docs_links", {"renderer": cfg.docs_renderer}):
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
    from .telemetry import trace_operation

    with trace_operation("mcp.server.create", {}):
        cfg = load_config()

        with trace_operation("mcp.fastmcp.init", {}):
            mcp = FastMCP(name="caitlyn-openapi-mcp")

        # Start loading OpenAPI spec in background (non-blocking)
        with trace_operation("mcp.background_loading.start", {}):
            _index_loader.start_loading_background(
                spec_url=cfg.spec_url,
                docs_renderer=cfg.docs_renderer,
                docs_base_url=cfg.docs_base_url,
            )

        # Register resources and tools - they will wait for index when called
        with trace_operation("mcp.register_handlers", {}):
            register_resources(mcp, index_loader=_index_loader)
            register_tools(mcp, index_loader=_index_loader)

        # Add request timing instrumentation
        _add_request_timing_instrumentation(mcp)

        logger.info("✓ Server ready (spec loading in background)")

        return mcp


def _add_request_timing_instrumentation(mcp: FastMCP) -> None:
    """Add OTEL tracing to track when MCP requests are received and processed."""
    from functools import wraps

    from .telemetry import get_tracer

    tracer = get_tracer()
    if tracer is None:
        logger.warning("Tracer not initialized, skipping request instrumentation")
        return

    # Track if we've seen the first request
    first_request_seen = {"value": False}

    # Wrap list_tools to add OTEL span
    original_list_tools = mcp.list_tools

    @wraps(original_list_tools)
    async def timed_list_tools(*args, **kwargs):
        is_first = not first_request_seen["value"]
        if is_first:
            first_request_seen["value"] = True
            logger.info("🔔 First MCP request received: list_tools")

        with tracer.start_as_current_span("mcp.list_tools") as span:
            span.set_attribute("mcp.method", "list_tools")
            span.set_attribute("mcp.first_request", is_first)
            result = await original_list_tools(*args, **kwargs)
            return result

    mcp.list_tools = timed_list_tools

    # Wrap list_resources to add OTEL span
    original_list_resources = mcp.list_resources

    @wraps(original_list_resources)
    async def timed_list_resources(*args, **kwargs):
        is_first = not first_request_seen["value"]
        if is_first:
            first_request_seen["value"] = True
            logger.info("🔔 First MCP request received: list_resources")

        with tracer.start_as_current_span("mcp.list_resources") as span:
            span.set_attribute("mcp.method", "list_resources")
            span.set_attribute("mcp.first_request", is_first)
            result = await original_list_resources(*args, **kwargs)
            return result

    mcp.list_resources = timed_list_resources

    # Wrap call_tool to add OTEL span
    original_call_tool = mcp.call_tool

    @wraps(original_call_tool)
    async def timed_call_tool(*args, **kwargs):
        is_first = not first_request_seen["value"]
        if is_first:
            first_request_seen["value"] = True
            logger.info("🔔 First MCP request received: call_tool")

        with tracer.start_as_current_span("mcp.call_tool") as span:
            span.set_attribute("mcp.method", "call_tool")
            span.set_attribute("mcp.first_request", is_first)
            result = await original_call_tool(*args, **kwargs)
            return result

    mcp.call_tool = timed_call_tool


def main() -> None:
    """
    Main entry point for the MCP server.

    Transport mode is configured via MCP_TRANSPORT environment variable:
    - "stdio" (default): For local development and Claude Desktop
    - "streamable-http": For Bedrock AgentCore deployment
    """
    import sys

    # Configure logging to stderr only
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )

    # Initialize OpenTelemetry
    setup_telemetry()

    # Now that OTEL is set up, use it to trace startup
    from .telemetry import get_tracer, trace_operation

    tracer = get_tracer()

    if tracer:
        with trace_operation("mcp.server.full_startup", {"mode": "stdio"}):
            cfg = load_config()
            mcp = create_server()

            logger.info("🚀 Starting MCP transport - ready for connections")

            with tracer.start_as_current_span("mcp.transport.run") as transport_span:
                transport_span.set_attribute("transport.type", cfg.transport)
                # Type assertion - config ensures this is a valid transport
                mcp.run(transport=cfg.transport)  # type: ignore[arg-type]
    else:
        # Fallback if OTEL not initialized
        cfg = load_config()
        mcp = create_server()
        logger.info("🚀 Starting MCP transport - ready for connections")
        mcp.run(transport=cfg.transport)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
