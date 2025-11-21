from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from .model import Endpoint

logger = logging.getLogger(__name__)

# Use a lightweight, high-quality model (only ~80MB)
MODEL_NAME = "all-MiniLM-L6-v2"


class VectorSearchIndex:
    """In-memory vector search index for endpoints using sentence transformers."""

    def __init__(self, endpoints: list[Endpoint]):
        """
        Initialize the vector search index.

        Args:
            endpoints: List of endpoints to index
        """
        logger.info(f"Initializing vector search with model: {MODEL_NAME}")
        self.model = SentenceTransformer(MODEL_NAME)
        self.endpoints = endpoints

        # Create searchable text for each endpoint
        self.texts = [self._create_search_text(ep) for ep in endpoints]

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(self.texts)} endpoints...")
        self.embeddings = self.model.encode(self.texts, show_progress_bar=False)
        logger.info("Vector search index ready")

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
        # Generate query embedding
        query_embedding = self.model.encode([query], show_progress_bar=False)[0]

        # Calculate cosine similarity
        similarities = self._cosine_similarity(query_embedding, self.embeddings)

        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # Filter out very low similarity scores (< 0.3)
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= min_similarity:  # Minimum similarity threshold
                results.append((self.endpoints[idx], score))

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
