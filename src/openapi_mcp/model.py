from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openapi_core import Spec


@dataclass
class Endpoint:
    path: str
    method: str  # "GET", "POST", etc.
    summary: str | None
    description: str | None
    operation_id: str | None
    tags: list[str]
    parameters: list[dict[str, Any]]
    request_body: dict[str, Any] | None
    responses: dict[str, Any]
    docs_url: str | None  # deep link into Scalar docs (if available)


@dataclass
class OpenApiIndex:
    spec: Spec
    raw: dict[str, Any]
    endpoints: list[Endpoint]
    schemas: dict[str, dict[str, Any]]
    security_schemes: dict[str, dict[str, Any]]
    spec_url: str
    # Optional docs deep-link maps (for schemas/security if desired)
    schema_docs_urls: dict[str, str]
    security_scheme_docs_urls: dict[str, str]
