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
    # Vector search index for semantic search (background-loaded)
    vector_index: VectorSearchIndex | None = None
    _vector_index_lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)
    _vector_index_initialized: bool = field(default=False, repr=False, compare=False)
    _vector_index_loading: bool = field(default=False, repr=False, compare=False)

    def start_loading_vector_index_background(self) -> None:
        """
        Start loading the vector search index in a background thread.
        This is called during server startup to pre-load the model without blocking.
        """
        if self._vector_index_initialized or self._vector_index_loading:
            return

        def _load_in_background():
            with self._vector_index_lock:
                if self._vector_index_initialized:
                    return

                self._vector_index_loading = True
                try:
                    logger.info("Starting background vector search index initialization...")
                    from .vector_search import VectorSearchIndex

                    self.vector_index = VectorSearchIndex(self.endpoints)
                    self._vector_index_initialized = True
                    logger.info("Vector search index ready for semantic search")
                except Exception as e:
                    logger.warning(f"Failed to create vector search index: {e}. Semantic search will be unavailable.")
                    self._vector_index_initialized = True  # Mark as attempted to avoid retrying
                finally:
                    self._vector_index_loading = False

        thread = threading.Thread(target=_load_in_background, daemon=True, name="vector-index-loader")
        thread.start()

    def ensure_vector_index(self) -> None:
        """
        Wait for vector search index to be ready (if still loading in background).
        If not started yet, initialize synchronously.
        Thread-safe via lock.
        """
        if self._vector_index_initialized:
            return

        # If loading in background, wait for it
        if self._vector_index_loading:
            logger.debug("Waiting for background vector index initialization to complete...")
            with self._vector_index_lock:
                # Lock will be released when background loading completes
                pass
            return

        # Not loading in background, initialize now (fallback case)
        with self._vector_index_lock:
            if self._vector_index_initialized:
                return

            try:
                logger.info("Initializing vector search index...")
                from .vector_search import VectorSearchIndex

                self.vector_index = VectorSearchIndex(self.endpoints)
                self._vector_index_initialized = True
                logger.info("Vector search index initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to create vector search index: {e}. Semantic search will be unavailable.")
                self._vector_index_initialized = True  # Mark as attempted to avoid retrying
