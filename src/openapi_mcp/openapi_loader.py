from __future__ import annotations

import json
import logging
from typing import Any, Iterable
from urllib.request import urlopen

import yaml
from openapi_core import Spec
from prance import ResolvingParser
from prance.util.url import ResolutionError

from .model import Endpoint, OpenApiIndex
from .vector_search import VectorSearchIndex

logger = logging.getLogger(__name__)


def _iter_operations(spec: Spec) -> Iterable[tuple[str, str, Any]]:
    """Iterate over all operations in the spec."""
    for path_name, path_item in spec.paths.items():
        for method_name, op in path_item.operations.items():
            yield path_name, method_name.upper(), op


def _iter_operations_from_dict(spec_dict: dict[str, Any]) -> Iterable[tuple[str, str, Any]]:
    """Iterate over all operations directly from spec dict (fallback for broken specs)."""
    paths = spec_dict.get("paths", {})
    for path_name, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method_name in ["get", "post", "put", "delete", "patch", "options", "head", "trace"]:
            if method_name in path_item:
                yield path_name, method_name.upper(), path_item[method_name]


def load_openapi_spec_from_url(spec_url: str) -> OpenApiIndex:
    """
    Load and parse an OpenAPI spec from a URL using Prance.

    Args:
        spec_url: Full URL to the OpenAPI JSON/YAML specification

    Returns:
        OpenApiIndex with parsed spec, endpoints, schemas, and security schemes
    """
    # Try to resolve all $refs (including remote refs)
    # If that fails due to broken refs, fall back to using spec without resolution
    try:
        parser = ResolvingParser(spec_url, backend="openapi-spec-validator", strict=False)
        resolved: dict[str, Any] = parser.specification
        logger.info(f"Successfully loaded and resolved OpenAPI spec from {spec_url}")

    except ResolutionError as e:
        # Broken $refs detected - load spec without resolution or validation
        logger.warning(
            f"OpenAPI spec has broken $refs: {e}. "
            f"Loading spec as-is without reference resolution. Some schemas may be incomplete."
        )
        # Fetch and parse the spec directly without Prance validation
        with urlopen(spec_url) as response:
            content = response.read().decode("utf-8")
            if spec_url.endswith((".yaml", ".yml")):
                resolved = yaml.safe_load(content)
            else:
                resolved = json.loads(content)

    except Exception as e:
        # If loading fails completely, provide a helpful error message
        logger.error(f"Failed to load OpenAPI spec: {e}")
        raise RuntimeError(
            f"Failed to load OpenAPI spec from {spec_url}. "
            f"The spec may be malformed or inaccessible. "
            f"Error: {e}"
        ) from e

    # Wrap in openapi-core Spec for structured access
    try:
        spec = Spec.from_dict(resolved)
    except Exception as e:
        logger.error(f"Failed to create Spec object from resolved spec: {e}")
        raise RuntimeError(
            f"OpenAPI spec structure is invalid. "
            f"Error: {e}"
        ) from e

    endpoints: list[Endpoint] = []

    # Extract all operations
    # Try using Spec object first, fallback to raw dict if that fails
    try:
        # Test if spec has paths attribute by accessing it
        _ = spec.paths
        operations_iter = _iter_operations(spec)
    except (AttributeError, Exception) as e:
        logger.warning(f"Spec object missing expected attributes, using raw dict fallback: {e}")
        # Try to extract directly from the raw dict if Spec object is broken
        operations_iter = _iter_operations_from_dict(resolved)

    for path_name, method, operation in operations_iter:
        # Handle both Spec operation objects and raw dicts
        if isinstance(operation, dict):
            op_raw = operation
        else:
            op_raw = getattr(operation, "_operation", operation)  # type: ignore[attr-defined]
            if not isinstance(op_raw, dict):
                op_raw = {}

        summary = op_raw.get("summary")
        description = op_raw.get("description")
        operation_id = op_raw.get("operationId")
        tags = list(op_raw.get("tags") or [])

        # Extract parameters
        parameters: list[dict[str, Any]] = []
        if isinstance(operation, dict):
            # Raw dict mode
            params_list = op_raw.get("parameters", [])
            if isinstance(params_list, list):
                parameters = [dict(p) if isinstance(p, dict) else {} for p in params_list]
        else:
            # Spec object mode
            for param in operation.parameters:
                param_raw = getattr(param, "_parameter", None)
                if isinstance(param_raw, dict):
                    parameters.append(dict(param_raw))

        # Extract request body
        request_body_raw: dict[str, Any] | None = None
        if isinstance(operation, dict):
            # Raw dict mode
            rb = op_raw.get("requestBody")
            if isinstance(rb, dict):
                request_body_raw = dict(rb)
        else:
            # Spec object mode
            if operation.request_body is not None:
                rb_raw = getattr(operation.request_body, "_request_body", None)
                if isinstance(rb_raw, dict):
                    request_body_raw = dict(rb_raw)

        # Extract responses
        responses_raw: dict[str, Any] = {}
        if isinstance(operation, dict):
            # Raw dict mode
            responses = op_raw.get("responses", {})
            if isinstance(responses, dict):
                responses_raw = {str(k): dict(v) if isinstance(v, dict) else {} for k, v in responses.items()}
        else:
            # Spec object mode
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

    # Vector index will be initialized lazily on first search to avoid blocking server startup
    return OpenApiIndex(
        spec=spec,
        raw=resolved,
        endpoints=endpoints,
        schemas=schemas,
        security_schemes=security_schemes,
        spec_url=spec_url,
        schema_docs_urls={},
        security_scheme_docs_urls={},
        vector_index=None,  # Lazy initialization
    )
