from __future__ import annotations

import logging
import threading
from typing import Protocol

from mcp.server.fastmcp import FastMCP

from .config import load_config
from .docs_links import attach_docs_links
from .model import OpenApiIndex
from .openapi_loader import load_openapi_spec_from_url
from .resources import register_resources
from .telemetry import setup_telemetry
from .tools import register_tools

logger = logging.getLogger(__name__)


class IndexLoaderProtocol(Protocol):
    """Protocol for objects that can load and provide OpenAPI indexes."""

    def get_index(self) -> OpenApiIndex:
        """Get the loaded index."""
        ...


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

        # Capture current trace context to propagate to background thread
        from opentelemetry import context

        current_context = context.get_current()

        def _load():
            from .telemetry import trace_operation

            # Attach the parent context in the background thread
            token = context.attach(current_context)
            try:
                # This will now be a child span of the startup trace
                with trace_operation("mcp.background.openapi_load", {"spec_url": spec_url}):
                    logger.info("Starting background OpenAPI spec load...")
                    cfg = load_config()

                    with trace_operation("openapi.load_spec_full", {"spec_url": cfg.spec_url}):
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
            finally:
                context.detach(token)

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
    # For AgentCore compatibility, use stateless_http=True when using streamable-http transport
    is_stateless = cfg.transport == "streamable-http"
    mcp = FastMCP(name="caitlyn-openapi-mcp", host="0.0.0.0", stateless_http=is_stateless)

    # Start loading OpenAPI spec in background (non-blocking)
    _index_loader.start_loading_background(
        spec_url=cfg.spec_url,
        docs_renderer=cfg.docs_renderer,
        docs_base_url=cfg.docs_base_url,
    )

    # Register resources and tools - they will wait for index when called
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

    # Wrap initialize to add OTEL span (this is the very first MCP protocol method called)
    if hasattr(mcp, "initialize"):
        original_initialize = mcp.initialize  # type: ignore[attr-defined]

        @wraps(original_initialize)
        async def timed_initialize(*args, **kwargs):
            first_request_seen["value"] = True
            logger.info("🔔 First MCP request received: initialize")

            from .telemetry import trace_operation_async

            with trace_operation_async(
                "mcp.initialize",
                {"mcp.method": "initialize", "mcp.first_request": True},
            ):
                result = await original_initialize(*args, **kwargs)
                return result

        mcp.initialize = timed_initialize  # type: ignore[attr-defined]

    # Wrap list_tools to add OTEL span
    original_list_tools = mcp.list_tools

    @wraps(original_list_tools)
    async def timed_list_tools(*args, **kwargs):
        is_first = not first_request_seen["value"]
        if is_first:
            first_request_seen["value"] = True
            logger.info("🔔 First MCP request received: list_tools")

        from .telemetry import trace_operation_async

        with trace_operation_async(
            "mcp.list_tools",
            {"mcp.method": "list_tools", "mcp.first_request": is_first},
            new_trace=True,
        ):
            result = await original_list_tools(*args, **kwargs)
            return result

    mcp.list_tools = timed_list_tools
    # Re-register the wrapped handler with the underlying MCP server
    mcp._mcp_server.list_tools()(timed_list_tools)

    # Wrap list_resources to add OTEL span
    original_list_resources = mcp.list_resources

    @wraps(original_list_resources)
    async def timed_list_resources(*args, **kwargs):
        is_first = not first_request_seen["value"]
        if is_first:
            first_request_seen["value"] = True
            logger.info("🔔 First MCP request received: list_resources")

        from .telemetry import trace_operation_async

        with trace_operation_async(
            "mcp.list_resources",
            {"mcp.method": "list_resources", "mcp.first_request": is_first},
            new_trace=True,
        ):
            result = await original_list_resources(*args, **kwargs)
            return result

    mcp.list_resources = timed_list_resources
    # Re-register the wrapped handler with the underlying MCP server
    mcp._mcp_server.list_resources()(timed_list_resources)

    # Wrap read_resource to add OTEL span
    original_read_resource = mcp.read_resource

    from pydantic import AnyUrl

    @wraps(original_read_resource)
    async def timed_read_resource(uri: AnyUrl | str, *args, **kwargs):  # type: ignore[no-untyped-def]
        is_first = not first_request_seen["value"]
        if is_first:
            first_request_seen["value"] = True
            logger.info("🔔 First MCP request received: read_resource")

        from .telemetry import trace_operation_async

        with trace_operation_async(
            "mcp.read_resource",
            {
                "mcp.method": "read_resource",
                "mcp.first_request": is_first,
                "resource.uri": uri,
            },
            new_trace=True,
        ):
            result = await original_read_resource(uri, *args, **kwargs)
            return result

    mcp.read_resource = timed_read_resource  # type: ignore[assignment]
    # Re-register the wrapped handler with the underlying MCP server
    mcp._mcp_server.read_resource()(timed_read_resource)  # type: ignore[arg-type]

    # Wrap call_tool to add OTEL span
    original_call_tool = mcp.call_tool

    @wraps(original_call_tool)
    async def timed_call_tool(name: str, arguments: dict, *args, **kwargs):
        is_first = not first_request_seen["value"]
        if is_first:
            first_request_seen["value"] = True
            logger.info("🔔 First MCP request received: call_tool")

        from .telemetry import trace_operation_async

        # Include tool name in the span name for better visibility in Jaeger
        span_name = f"mcp.call_tool.{name}"
        with trace_operation_async(
            span_name,
            {
                "mcp.method": "call_tool",
                "mcp.first_request": is_first,
                "tool.name": name,
                "tool.arguments": str(arguments),
            },
            new_trace=True,
        ):
            result = await original_call_tool(name, arguments, *args, **kwargs)
            return result

    mcp.call_tool = timed_call_tool
    # Re-register the wrapped handler with the underlying MCP server
    mcp._mcp_server.call_tool(validate_input=False)(timed_call_tool)


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
    from .telemetry import trace_operation

    cfg = load_config()

    # Single top-level trace for entire server initialization
    with trace_operation("mcp.server.startup", {"transport": cfg.transport}):
        mcp = create_server()
        logger.info("🚀 Starting MCP transport - ready for connections")

    # Run transport outside the initialization trace
    # This allows protocol requests to be separate traces
    mcp.run(transport=cfg.transport)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
