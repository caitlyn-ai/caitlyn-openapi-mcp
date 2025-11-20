from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    spec_url: str
    docs_renderer: str
    docs_base_url: str | None
    transport: str


def load_config() -> AppConfig:
    spec_url = os.environ.get("OPENAPI_SPEC_URL")
    if not spec_url:
        raise RuntimeError("OPENAPI_SPEC_URL is required (URL to OpenAPI JSON/YAML).")

    docs_renderer = os.environ.get("DOCS_RENDERER", "scalar").lower()
    docs_base_url = os.environ.get("DOCS_BASE_URL")  # e.g. https://api.example.com/scalar

    # Transport mode: "stdio" for local dev/Claude Desktop, "streamable-http" for Bedrock
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    if transport not in ("stdio", "streamable-http"):
        raise RuntimeError(f"Invalid MCP_TRANSPORT: {transport}. Must be 'stdio' or 'streamable-http'.")

    return AppConfig(
        spec_url=spec_url,
        docs_renderer=docs_renderer,
        docs_base_url=docs_base_url,
        transport=transport,
    )
