from __future__ import annotations

from urllib.parse import quote

from .model import Endpoint, OpenApiIndex


def attach_docs_links(index: OpenApiIndex, *, renderer: str, base_url: str | None) -> None:
    """
    Mutates `index` in-place to add docs_url fields for endpoints/schemas/security schemes
    according to the given docs renderer.

    For now, only 'scalar' is supported. If base_url is None, this is a no-op.

    Args:
        index: The OpenApiIndex to decorate with docs URLs
        renderer: The docs renderer type (currently only "scalar" is supported)
        base_url: Base URL of the docs UI (e.g. https://api.example.com/docs or /scalar)
    """
    if not base_url:
        return

    if renderer == "scalar":
        _attach_scalar_links(index, base_url=base_url)


def _scalar_endpoint_link(base_url: str, ep: Endpoint) -> str:
    """
    Generate a Scalar deep link for an endpoint.

    Format: {base_url}#tag/{tag}/{methodLower}/{path}
    Example: https://betty.getcaitlyn.ai/api/docs#tag/knowledge-bases/post/v1/knowledge-bases

    Args:
        base_url: Base URL of the Scalar UI
        ep: The endpoint to generate a link for

    Returns:
        Full deep link URL to the endpoint in Scalar
    """
    tag = ep.tags[0] if ep.tags else "default"
    method_lower = ep.method.lower()
    # keep / and {} and - as-is; encode other weirdness
    encoded_path = quote(ep.path.lstrip("/"), safe="/{}-")
    return f"{base_url}#tag/{tag}/{method_lower}/{encoded_path}"


def _attach_scalar_links(index: OpenApiIndex, *, base_url: str) -> None:
    """
    Attach Scalar documentation deep links to all items in the index.

    Args:
        index: The OpenApiIndex to decorate
        base_url: Base URL of the Scalar UI
    """
    # Attach endpoint deep links
    for ep in index.endpoints:
        ep.docs_url = _scalar_endpoint_link(base_url, ep)

    # Attach schema deep links
    schema_links: dict[str, str] = {}
    for name in index.schemas.keys():
        schema_links[name] = f"{base_url}#schema/{quote(name, safe='-_.')}"
    index.schema_docs_urls = schema_links

    # Attach security scheme deep links
    sec_links: dict[str, str] = {}
    for name in index.security_schemes.keys():
        sec_links[name] = f"{base_url}#security/{quote(name, safe='-_.')}"
    index.security_scheme_docs_urls = sec_links
