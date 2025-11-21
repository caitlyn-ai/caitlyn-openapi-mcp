"""OpenTelemetry instrumentation for MCP server."""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer: trace.Tracer | None = None


def setup_telemetry(service_name: str = "caitlyn-openapi-mcp") -> None:
    """
    Initialize OpenTelemetry tracing.

    Configured via environment variables:
    - OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (default: http://localhost:4317)
    - OTEL_SERVICE_NAME: Service name (default: caitlyn-openapi-mcp)
    - ENABLE_TELEMETRY: Enable/disable telemetry (default: true)
    """
    global _tracer

    # Check if telemetry is disabled
    if os.environ.get("ENABLE_TELEMETRY", "true").lower() == "false":
        logger.info("Telemetry disabled via ENABLE_TELEMETRY=false")
        return

    try:
        # Get service name from env or use default
        service_name = os.environ.get("OTEL_SERVICE_NAME", service_name)

        # Create resource
        resource = Resource(attributes={"service.name": service_name})

        # Set up trace provider
        provider = TracerProvider(resource=resource)

        # Get OTLP endpoint
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

        if otlp_endpoint:
            # Add OTLP exporter if endpoint is configured
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info(f"✓ OpenTelemetry configured with OTLP endpoint: {otlp_endpoint}")
        else:
            # No exporter configured - traces will be collected but not exported
            # (Console exporter is not compatible with MCP stdio transport)
            logger.info("✓ OpenTelemetry initialized (no OTLP endpoint configured)")

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer instance
        _tracer = trace.get_tracer(__name__)

    except Exception as e:
        logger.warning(f"Failed to initialize OpenTelemetry: {e}. Telemetry will be disabled.")


def get_tracer() -> trace.Tracer | None:
    """Get the global tracer instance."""
    return _tracer


@contextmanager
def trace_operation(operation_name: str, attributes: dict[str, Any] | None = None):
    """
    Context manager for tracing operations.

    Usage:
        with trace_operation("load_openapi_spec", {"spec_url": url}):
            # Your code here
            pass
    """
    tracer = get_tracer()
    if tracer is None:
        # Telemetry not initialized, just yield
        yield None
        return

    with tracer.start_as_current_span(operation_name) as span:
        if attributes:
            span.set_attributes(attributes)
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise
