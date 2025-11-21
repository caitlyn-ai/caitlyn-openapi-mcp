from __future__ import annotations

import hashlib
import logging
import os
import pickle
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from .model import Endpoint

logger = logging.getLogger(__name__)

# Use a lightweight, high-quality model (only ~80MB)
MODEL_NAME = "all-MiniLM-L6-v2"


class VectorSearchIndex:
    """In-memory vector search index for endpoints using sentence transformers."""

    def __init__(self, endpoints: list[Endpoint], cache_dir: str | None = None):
        """
        Initialize the vector search index.

        Args:
            endpoints: List of endpoints to index
            cache_dir: Directory to cache embeddings (default: ./models/cache/)
        """
        logger.info(f"Initializing vector search with model: {MODEL_NAME}")
        self.model = SentenceTransformer(MODEL_NAME)
        self.endpoints = endpoints

        # Create searchable text for each endpoint
        self.texts = [self._create_search_text(ep) for ep in endpoints]

        # Set up cache directory
        if cache_dir is None:
            cache_dir = os.environ.get("SENTENCE_TRANSFORMERS_HOME", "./models")
        self.cache_dir = Path(cache_dir) / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Try to load from cache, otherwise generate
        cache_key = self._compute_cache_key(self.texts)
        cache_path = self.cache_dir / f"embeddings_{cache_key}.pkl"

        if cache_path.exists():
            logger.info(f"Loading cached embeddings from {cache_path}...")
            try:
                with open(cache_path, "rb") as f:
                    self.embeddings = pickle.load(f)
                logger.info("✓ Loaded embeddings from cache (fast cold-start)")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}. Regenerating embeddings...")
                self.embeddings = self._generate_and_cache_embeddings(cache_path)
        else:
            logger.info(f"No cache found. Generating embeddings for {len(self.texts)} endpoints...")
            self.embeddings = self._generate_and_cache_embeddings(cache_path)

    def _compute_cache_key(self, texts: list[str]) -> str:
        """Compute a cache key based on endpoint texts."""
        # Hash all texts together to create a unique key
        content = "|".join(sorted(texts))
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _generate_and_cache_embeddings(self, cache_path: Path) -> np.ndarray:
        """Generate embeddings and save to cache."""
        with trace_operation("vector_search.generate_embeddings", {"text_count": len(self.texts)}):
            embeddings = self.model.encode(self.texts, show_progress_bar=False)

        # Save to cache
        try:
            with open(cache_path, "wb") as f:
                pickle.dump(embeddings, f)
            logger.info(f"✓ Cached embeddings to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to cache embeddings: {e}")

        logger.info("Vector search index ready")
        return embeddings

    def _create_search_text(self, endpoint: Endpoint) -> str:
        """Create searchable text representation of an endpoint."""
        parts = [
            endpoint.method,
            endpoint.path,
            endpoint.summary or "",
            endpoint.description or "",
            endpoint.operation_id or "",
            " ".join(endpoint.tags),
        ]
        return " ".join(filter(None, parts))

    def search(self, query: str, top_k: int = 20, min_similarity: float = 0.5) -> list[tuple[Endpoint, float]]:
        """
        Search for endpoints using vector similarity.

        Args:
            query: Search query
            top_k: Maximum number of results to return

        Returns:
            List of (endpoint, similarity_score) tuples, sorted by relevance
        """
        with trace_operation("vector_search.search", {"query": query, "top_k": top_k}) as span:
            # Generate query embedding
            query_embedding = self.model.encode([query], show_progress_bar=False)[0]

            # Calculate cosine similarity
            similarities = self._cosine_similarity(query_embedding, self.embeddings)

            # Get top-k results
            top_indices = np.argsort(similarities)[::-1][:top_k]

            # Filter out very low similarity scores
            results = []
            for idx in top_indices:
                score = float(similarities[idx])
                if score >= min_similarity:  # Minimum similarity threshold
                    results.append((self.endpoints[idx], score))

            if span:
                span.set_attribute("result_count", len(results))

            logger.debug(f"Vector search for '{query}' returned {len(results)} results")
            return results

    @staticmethod
    def _cosine_similarity(query_embedding: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity between query and all embeddings."""
        # Normalize vectors
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        # Calculate cosine similarity
        similarities = np.dot(embeddings_norm, query_norm)
        return similarities
