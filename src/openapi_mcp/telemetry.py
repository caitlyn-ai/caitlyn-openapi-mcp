"""OpenTelemetry instrumentation for MCP server."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult

logger = logging.getLogger(__name__)


class FileSpanExporter(SpanExporter):
    """Export spans to a JSON file for debugging."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        # Clear file on initialization
        with open(self.file_path, "w") as f:
            f.write("[\n")
        self._first_span = True

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans to file."""
        try:
            with open(self.file_path, "a") as f:
                for span in spans:
                    # Calculate duration if both times are available
                    duration_ms = None
                    if span.start_time is not None and span.end_time is not None:
                        duration_ms = (span.end_time - span.start_time) / 1_000_000  # ns to ms

                    span_data = {
                        "name": span.name,
                        "start_time": span.start_time,
                        "end_time": span.end_time,
                        "duration_ms": duration_ms,
                        "attributes": dict(span.attributes) if span.attributes else {},
                    }
                    if not self._first_span:
                        f.write(",\n")
                    else:
                        self._first_span = False
                    json.dump(span_data, f, indent=2)
            return SpanExportResult.SUCCESS
        except Exception as e:
            logger.error(f"Failed to export spans to file: {e}")
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        """Close the file."""
        try:
            with open(self.file_path, "a") as f:
                f.write("\n]\n")
        except Exception:
            pass


# Global tracer instance
_tracer: trace.Tracer | None = None


def setup_telemetry(service_name: str = "caitlyn-openapi-mcp") -> None:
    """
    Initialize OpenTelemetry tracing and logging.

    Configured via environment variables:
    - AGENTCORE_RUNTIME: If "true", skip manual OTEL setup (ADOT auto-instruments)
    - OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (default: http://localhost:4317)
    - OTEL_SERVICE_NAME: Service name (default: caitlyn-openapi-mcp)
    - OTEL_FILE_EXPORT: Path to export spans as JSON (default: ./mcp-spans.json)
    - ENABLE_TELEMETRY: Enable/disable telemetry (default: true)
    """
    global _tracer

    # Check if running in AgentCore runtime (ADOT auto-instruments)
    if os.environ.get("AGENTCORE_RUNTIME", "false").lower() == "true":
        logger.info("Running in AgentCore runtime - ADOT will auto-instrument (skipping manual OTEL setup)")
        # Still set up a basic tracer for our code to use
        _tracer = trace.get_tracer(__name__)
        return

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

        # Add file exporter if configured (useful for debugging)
        file_export_path = os.environ.get("OTEL_FILE_EXPORT", os.path.join(os.getcwd(), "mcp-spans.json"))
        file_exporter = FileSpanExporter(file_export_path)
        provider.add_span_processor(BatchSpanProcessor(file_exporter))
        logger.info(f"✓ OpenTelemetry file export enabled: {file_export_path}")

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer instance
        _tracer = trace.get_tracer(__name__)

        # Set up metrics with gRPC exporter (if OTLP endpoint configured)
        if otlp_endpoint:
            metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
            metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=60000)
            meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
            from opentelemetry import metrics

            metrics.set_meter_provider(meter_provider)
            logger.info("✓ OpenTelemetry metrics configured with gRPC")

        # Set up logging integration
        logger_provider = LoggerProvider(resource=resource)

        if otlp_endpoint:
            # Add OTLP log exporter to send logs to the same endpoint as traces
            otlp_log_exporter = OTLPLogExporter(endpoint=otlp_endpoint, insecure=True)
            logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))
            logger.info(f"✓ OpenTelemetry logging configured with OTLP endpoint: {otlp_endpoint}")

        # Add OTEL logging handler to root logger to capture all log messages
        handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
        logging.getLogger().addHandler(handler)
        logger.info("✓ OpenTelemetry logging integration enabled")

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


@contextmanager
def trace_operation_async(operation_name: str, attributes: dict[str, Any] | None = None, new_trace: bool = False):
    """
    Context manager for tracing async operations.

    Use this in async functions to ensure proper span context propagation.

    Args:
        operation_name: Name of the operation being traced
        attributes: Optional attributes to attach to the span
        new_trace: If True, start a new trace (root span) instead of a child span

    Usage:
        async def my_async_function():
            with trace_operation_async("my_operation", {"key": "value"}):
                # Your async code here
                await something()
    """
    tracer = get_tracer()
    if tracer is None:
        # Telemetry not initialized, just yield
        yield None
        return

    # For MCP protocol requests, we want new traces, not child spans
    if new_trace:
        # Start a new trace by detaching from the current context
        from opentelemetry import context

        # Create a new context without any parent
        token = context.attach(context.Context())
        try:
            with tracer.start_as_current_span(operation_name) as span:
                if attributes:
                    span.set_attributes(attributes)
                try:
                    yield span
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        finally:
            context.detach(token)
    else:
        # Normal child span
        with tracer.start_as_current_span(operation_name) as span:
            if attributes:
                span.set_attributes(attributes)
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
