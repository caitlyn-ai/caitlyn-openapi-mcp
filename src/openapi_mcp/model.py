from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from openapi_core import Spec

if TYPE_CHECKING:
    from .vector_search import VectorSearchIndex

logger = logging.getLogger(__name__)


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
    # Vector search index for semantic search (lazy-loaded)
    vector_index: VectorSearchIndex | None = None
    _vector_index_lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)
    _vector_index_initialized: bool = field(default=False, repr=False, compare=False)

    def ensure_vector_index(self) -> None:
        """
        Lazily initialize the vector search index on first use.
        This avoids blocking server startup with model loading.
        Thread-safe via lock.
        """
        if self._vector_index_initialized:
            return

        with self._vector_index_lock:
            # Double-check pattern
            if self._vector_index_initialized:
                return

            try:
                logger.info("Initializing vector search index (this may take a moment)...")
                from .vector_search import VectorSearchIndex

                self.vector_index = VectorSearchIndex(self.endpoints)
                self._vector_index_initialized = True
                logger.info("Vector search index initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to create vector search index: {e}. Semantic search will be unavailable.")
                self._vector_index_initialized = True  # Mark as attempted to avoid retrying
