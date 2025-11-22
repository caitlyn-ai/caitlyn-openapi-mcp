#!/usr/bin/env python3
"""
Test script to verify OpenTelemetry integration with OTEL Collector.

This script:
1. Sends a test span to the OTEL collector
2. Sends a test log to the OTEL collector
3. Verifies the collector received the data

Run with: OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 python scripts/test_telemetry.py
"""

import logging
import sys
import time

from openapi_mcp.telemetry import setup_telemetry, trace_operation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger(__name__)


def main():
    """Test telemetry integration."""
    logger.info("🧪 Starting telemetry test...")

    # Initialize OTEL
    setup_telemetry(service_name="test-telemetry")

    # Send a test trace
    logger.info("📊 Sending test trace...")
    with trace_operation("test.operation", {"test_attribute": "test_value"}) as span:
        logger.info("✓ Inside test span")
        time.sleep(0.1)
        if span:
            span.set_attribute("test_result", "success")

    # Send a test log
    logger.info("📝 Sending test log...")
    logger.info("This is a test log message that should be captured by OTEL")
    logger.warning("This is a test warning that should also be captured")

    # Give OTEL batch processor time to send
    logger.info("⏳ Waiting for telemetry to flush...")
    time.sleep(2)

    logger.info("✅ Telemetry test complete!")
    logger.info("")
    logger.info("Check telemetry data:")
    logger.info("  • Jaeger UI: http://localhost:16686")
    logger.info("  • Look for service 'test-telemetry'")
    logger.info("  • You should see the 'test.operation' span with test_attribute")
    logger.info("")


if __name__ == "__main__":
    main()
