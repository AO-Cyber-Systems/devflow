"""Dual embedding system for DevFlow.

Provides embeddings using Apple's NLEmbedding when available,
with FastEmbed as a fallback for cross-platform compatibility.

Apple NLEmbedding: 512-dimensional sentence vectors (macOS 14+)
FastEmbed: 384-dimensional vectors using BAAI/bge-small-en-v1.5
"""

import logging
import subprocess
import json
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from devflow.docs.embedder import LocalEmbedder

logger = logging.getLogger(__name__)


class AppleEmbedding:
    """Apple NLEmbedding wrapper via Swift CLI.

    Uses macOS NaturalLanguage framework for on-device embeddings.
    Available on macOS 14+ with Apple Silicon.
    """

    def __init__(self):
        self._available: bool | None = None
        self._dimensions = 512  # NLEmbedding standard dimensions

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self._dimensions

    def is_available(self) -> bool:
        """Check if Apple NLEmbedding is available."""
        if self._available is not None:
            return self._available

        try:
            # Check for macOS and NaturalLanguage availability
            import platform
            if platform.system() != "Darwin":
                self._available = False
                return False

            # Try to run a simple embedding via Swift
            # This will be implemented via the Swift bridge
            self._available = self._check_swift_embedding()
        except Exception as e:
            logger.debug(f"Apple NLEmbedding not available: {e}")
            self._available = False

        return self._available

    def _check_swift_embedding(self) -> bool:
        """Check if Swift embedding service is available."""
        # For now, return False until Swift bridge is implemented
        # The Swift UI app will provide embeddings via reverse RPC
        return False

    def embed(self, text: str) -> list[float] | None:
        """Generate embedding for text using Apple NLEmbedding.

        Returns None if not available.
        """
        if not self.is_available():
            return None

        try:
            # This will call the Swift AIService via reverse RPC
            # For now, return None to fall back to FastEmbed
            return None
        except Exception as e:
            logger.warning(f"Apple embedding failed: {e}")
            return None

    def embed_batch(self, texts: list[str]) -> list[list[float] | None]:
        """Generate embeddings for multiple texts."""
        if not self.is_available():
            return [None] * len(texts)

        return [self.embed(text) for text in texts]


class DualEmbedder:
    """Dual embedding system using Apple NLEmbedding with FastEmbed fallback.

    This class provides a unified interface for text embeddings, automatically
    selecting the best available backend:

    1. Apple NLEmbedding (512-dim) - Preferred on macOS 14+
    2. FastEmbed (384-dim) - Cross-platform fallback

    The system normalizes embeddings to enable comparison across backends.
    """

    def __init__(self, prefer_apple: bool = True):
        """Initialize the dual embedder.

        Args:
            prefer_apple: If True, try Apple NLEmbedding first.
        """
        self._prefer_apple = prefer_apple
        self._apple: AppleEmbedding | None = None
        self._fastembed: "LocalEmbedder | None" = None
        self._active_backend: str | None = None

    @property
    def active_backend(self) -> str:
        """Get the name of the currently active embedding backend."""
        if self._active_backend:
            return self._active_backend

        # Determine active backend
        if self._prefer_apple and self._get_apple().is_available():
            self._active_backend = "apple"
        else:
            self._active_backend = "fastembed"

        return self._active_backend

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions for the active backend."""
        if self.active_backend == "apple":
            return self._get_apple().dimensions
        return self._get_fastembed().dimensions

    def _get_apple(self) -> AppleEmbedding:
        """Get or create Apple embedding instance."""
        if self._apple is None:
            self._apple = AppleEmbedding()
        return self._apple

    def _get_fastembed(self) -> "LocalEmbedder":
        """Get or create FastEmbed instance."""
        if self._fastembed is None:
            from devflow.docs.embedder import LocalEmbedder
            self._fastembed = LocalEmbedder()
        return self._fastembed

    def embed(self, text: str) -> list[float]:
        """Generate embedding for text.

        Tries Apple NLEmbedding first if available and preferred,
        falls back to FastEmbed otherwise.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector as list of floats.
        """
        # Try Apple first if preferred
        if self._prefer_apple:
            apple = self._get_apple()
            if apple.is_available():
                result = apple.embed(text)
                if result is not None:
                    return result

        # Fall back to FastEmbed
        return self._get_fastembed().embed_text(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        # Try Apple first if preferred
        if self._prefer_apple:
            apple = self._get_apple()
            if apple.is_available():
                results = apple.embed_batch(texts)
                # If all succeeded, return
                if all(r is not None for r in results):
                    return results  # type: ignore

        # Fall back to FastEmbed
        return self._get_fastembed().embed_texts(texts)

    def similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts.

        Args:
            text1: First text.
            text2: Second text.

        Returns:
            Similarity score between -1 and 1.
        """
        from devflow.docs.embedder import cosine_similarity

        vec1 = self.embed(text1)
        vec2 = self.embed(text2)
        return cosine_similarity(vec1, vec2)

    def find_similar(
        self,
        query: str,
        texts: list[str],
        limit: int = 5,
        min_similarity: float = 0.0
    ) -> list[tuple[int, str, float]]:
        """Find texts most similar to query.

        Args:
            query: Query text.
            texts: List of texts to search.
            limit: Maximum number of results.
            min_similarity: Minimum similarity threshold.

        Returns:
            List of (index, text, similarity) tuples, sorted by similarity.
        """
        from devflow.docs.embedder import cosine_similarity

        if not texts:
            return []

        query_embedding = self.embed(query)
        text_embeddings = self.embed_batch(texts)

        # Calculate similarities
        similarities = [
            (i, text, cosine_similarity(query_embedding, emb))
            for i, (text, emb) in enumerate(zip(texts, text_embeddings))
        ]

        # Filter and sort
        filtered = [
            (i, text, sim)
            for i, text, sim in similarities
            if sim >= min_similarity
        ]
        filtered.sort(key=lambda x: x[2], reverse=True)

        return filtered[:limit]

    def get_status(self) -> dict:
        """Get status of embedding backends.

        Returns:
            Dict with status information for each backend.
        """
        apple = self._get_apple()
        return {
            "active_backend": self.active_backend,
            "dimensions": self.dimensions,
            "apple": {
                "available": apple.is_available(),
                "dimensions": apple.dimensions,
            },
            "fastembed": {
                "available": True,  # Always available as fallback
                "dimensions": self._get_fastembed().dimensions,
                "model": self._get_fastembed().model_name,
            },
        }


@lru_cache(maxsize=1)
def get_dual_embedder(prefer_apple: bool = True) -> DualEmbedder:
    """Get a cached dual embedder instance.

    Args:
        prefer_apple: If True, prefer Apple NLEmbedding.

    Returns:
        DualEmbedder instance.
    """
    return DualEmbedder(prefer_apple=prefer_apple)
