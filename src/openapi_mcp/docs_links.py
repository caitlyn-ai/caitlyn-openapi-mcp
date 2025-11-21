from __future__ import annotations

import re
from urllib.parse import quote

from .model import Endpoint, OpenApiIndex


def _slugify(text: str) -> str:
    """
    Convert text to a URL-safe slug (lowercase, hyphens, alphanumeric).

    Example: "Caitlyn API" -> "caitlyn-api"
    """
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and underscores with hyphens
    text = re.sub(r"[\s_]+", "-", text)
    # Remove non-alphanumeric characters except hyphens
    text = re.sub(r"[^a-z0-9-]", "", text)
    # Remove consecutive hyphens
    text = re.sub(r"-+", "-", text)
    # Strip leading/trailing hyphens
    return text.strip("-")


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


def _scalar_endpoint_link(base_url: str, ep: Endpoint, api_prefix: str | None = None) -> str:
    """
    Generate a Scalar deep link for an endpoint.

    Format: {base_url}#{api_prefix}/tag/{tag}/{methodLower}/{path}
    Example: https://betty.getcaitlyn.ai/api/docs#caitlyn-api-v1/tag/chat/post/v1/bedrock/agent/{agentId}/{agentAliasId}/{sessionId}

    Args:
        base_url: Base URL of the Scalar UI
        ep: The endpoint to generate a link for
        api_prefix: Optional API version prefix (e.g., "caitlyn-api-v1")

    Returns:
        Full deep link URL to the endpoint in Scalar
    """
    tag = _slugify(ep.tags[0]) if ep.tags else "default"
    method_lower = ep.method.lower()
    # keep / and {} and - as-is; encode other weirdness
    encoded_path = quote(ep.path.lstrip("/"), safe="/{}-")

    if api_prefix:
        return f"{base_url}#{api_prefix}/tag/{tag}/{method_lower}/{encoded_path}"
    else:
        return f"{base_url}#tag/{tag}/{method_lower}/{encoded_path}"


def _attach_scalar_links(index: OpenApiIndex, *, base_url: str) -> None:
    """
    Attach Scalar documentation deep links to all items in the index.

    Args:
        index: The OpenApiIndex to decorate
        base_url: Base URL of the Scalar UI
    """
    # Extract API prefix from OpenAPI spec info
    api_prefix: str | None = None
    info = index.raw.get("info", {})
    if info:
        title = info.get("title", "")
        version = info.get("version", "")

        # Create slug from title and version (e.g., "Caitlyn API" + "v1" -> "caitlyn-api-v1")
        if title:
            title_slug = _slugify(title)
            if version:
                # Extract major version if it's semantic (e.g., "1.0.0" -> "v1")
                version_slug = version
                if "." in version and not version.startswith("v"):
                    major_version = version.split(".")[0]
                    version_slug = f"v{major_version}"
                elif not version.startswith("v"):
                    version_slug = f"v{version}"
                else:
                    version_slug = _slugify(version)

                api_prefix = f"{title_slug}-{version_slug}"
            else:
                api_prefix = title_slug

    # Attach endpoint deep links
    for ep in index.endpoints:
        ep.docs_url = _scalar_endpoint_link(base_url, ep, api_prefix=api_prefix)

    # Attach schema deep links
    schema_links: dict[str, str] = {}
    for name in index.schemas.keys():
        if api_prefix:
            schema_links[name] = f"{base_url}#{api_prefix}/schema/{quote(name, safe='-_.')}"
        else:
            schema_links[name] = f"{base_url}#schema/{quote(name, safe='-_.')}"
    index.schema_docs_urls = schema_links

    # Attach security scheme deep links
    sec_links: dict[str, str] = {}
    for name in index.security_schemes.keys():
        if api_prefix:
            sec_links[name] = f"{base_url}#{api_prefix}/security/{quote(name, safe='-_.')}"
        else:
            sec_links[name] = f"{base_url}#security/{quote(name, safe='-_.')}"
    index.security_scheme_docs_urls = sec_links
