from __future__ import annotations

from typing import Any, Iterable

from openapi_core import Spec
from openapi_core.spec.operations import SpecOperation
from openapi_core.spec.paths import SpecPathItem
from prance import ResolvingParser

from .model import Endpoint, OpenApiIndex


def _iter_operations(spec: Spec) -> Iterable[tuple[str, str, SpecOperation]]:
    """Iterate over all operations in the spec."""
    for path_name, path_item in spec.paths.items():
        assert isinstance(path_item, SpecPathItem)
        for method_name, op in path_item.operations.items():
            yield path_name, method_name.upper(), op


def load_openapi_spec_from_url(spec_url: str) -> OpenApiIndex:
    """
    Load and parse an OpenAPI spec from a URL using Prance.

    Args:
        spec_url: Full URL to the OpenAPI JSON/YAML specification

    Returns:
        OpenApiIndex with parsed spec, endpoints, schemas, and security schemes
    """
    # Use Prance to resolve all $refs (including remote refs)
    parser = ResolvingParser(spec_url, backend="openapi-spec-validator")
    resolved: dict[str, Any] = parser.specification

    # Wrap in openapi-core Spec for structured access
    spec = Spec.from_dict(resolved)

    endpoints: list[Endpoint] = []

    # Extract all operations
    for path_name, method, operation in _iter_operations(spec):
        op_raw = operation._operation  # type: ignore[attr-defined]

        summary = op_raw.get("summary")
        description = op_raw.get("description")
        operation_id = op_raw.get("operationId")
        tags = list(op_raw.get("tags") or [])

        # Extract parameters
        parameters: list[dict[str, Any]] = []
        for param in operation.parameters:
            param_raw = getattr(param, "_parameter", None)
            if isinstance(param_raw, dict):
                parameters.append(dict(param_raw))

        # Extract request body
        request_body_raw: dict[str, Any] | None = None
        if operation.request_body is not None:
            rb_raw = getattr(operation.request_body, "_request_body", None)
            if isinstance(rb_raw, dict):
                request_body_raw = dict(rb_raw)

        # Extract responses
        responses_raw: dict[str, Any] = {}
        for status_code, response in operation.responses.items():
            resp_raw = getattr(response, "_response", None)
            if isinstance(resp_raw, dict):
                responses_raw[str(status_code)] = dict(resp_raw)

        endpoints.append(
            Endpoint(
                path=path_name,
                method=method,
                summary=summary,
                description=description,
                operation_id=operation_id,
                tags=tags,
                parameters=parameters,
                request_body=request_body_raw,
                responses=responses_raw,
                docs_url=None,  # filled in by docs_links.py later
            )
        )

    # Extract components
    components: dict[str, Any] = resolved.get("components") or {}
    schemas: dict[str, dict[str, Any]] = dict(components.get("schemas") or {})
    security_schemes: dict[str, dict[str, Any]] = dict(components.get("securitySchemes") or {})

    return OpenApiIndex(
        spec=spec,
        raw=resolved,
        endpoints=endpoints,
        schemas=schemas,
        security_schemes=security_schemes,
        spec_url=spec_url,
        schema_docs_urls={},
        security_scheme_docs_urls={},
    )
