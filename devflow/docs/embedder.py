"""Local embedding generation using FastEmbed.

FastEmbed is a lightweight, ONNX-based embedding library that runs entirely
offline without requiring PyTorch or cloud API calls.

Required dependencies:
- numpy: pip install numpy
- fastembed: pip install fastembed
"""

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None  # type: ignore

if TYPE_CHECKING:
    from fastembed import TextEmbedding

logger = logging.getLogger(__name__)

# Default model - BGE-small is lightweight (~33MB) with good quality
DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_DIMENSIONS = 384


class LocalEmbedder:
    """Local text embedding using FastEmbed.

    Uses ONNX-based models that run entirely offline.
    Default model: bge-small-en-v1.5 (384 dimensions, ~33MB)
    """

    def __init__(self, model_name: str = DEFAULT_MODEL):
        """Initialize the embedder.

        Args:
            model_name: The FastEmbed model to use. Default is bge-small-en-v1.5.
        """
        self.model_name = model_name
        self._model: "TextEmbedding | None" = None
        self._dimensions = DEFAULT_DIMENSIONS

    @property
    def dimensions(self) -> int:
        """Get the embedding dimensions for the current model."""
        return self._dimensions

    def _get_model(self) -> "TextEmbedding":
        """Lazy-load the embedding model."""
        if self._model is None:
            try:
                from fastembed import TextEmbedding

                logger.info(f"Loading embedding model: {self.model_name}")
                self._model = TextEmbedding(model_name=self.model_name)
                logger.info("Embedding model loaded successfully")
            except ImportError:
                raise ImportError(
                    "FastEmbed is required for embeddings. "
                    "Install with: pip install fastembed"
                )
        return self._model

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: The text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        model = self._get_model()
        # FastEmbed returns a generator, we need to get the first result
        embeddings = list(model.embed([text]))
        return embeddings[0].tolist()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        model = self._get_model()
        embeddings = list(model.embed(texts))
        return [emb.tolist() for emb in embeddings]

    def embed_document(
        self,
        content: str,
        title: str | None = None,
        description: str | None = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ) -> list[tuple[str, list[float]]]:
        """Embed a document, optionally chunking large content.

        Args:
            content: The document content.
            title: Optional title to prepend to chunks.
            description: Optional description to include.
            chunk_size: Maximum characters per chunk.
            chunk_overlap: Overlap between chunks for context continuity.

        Returns:
            List of (chunk_text, embedding) tuples.
        """
        # Build context prefix
        prefix_parts = []
        if title:
            prefix_parts.append(f"Title: {title}")
        if description:
            prefix_parts.append(f"Description: {description}")
        prefix = "\n".join(prefix_parts) + "\n\n" if prefix_parts else ""

        # Chunk the content if needed
        chunks = self._chunk_text(content, chunk_size, chunk_overlap)

        # Add prefix to first chunk only (to avoid redundancy)
        if chunks and prefix:
            chunks[0] = prefix + chunks[0]

        # Generate embeddings
        embeddings = self.embed_texts(chunks)

        return list(zip(chunks, embeddings))

    def _chunk_text(
        self, text: str, chunk_size: int, overlap: int
    ) -> list[str]:
        """Split text into overlapping chunks.

        Args:
            text: Text to chunk.
            chunk_size: Maximum characters per chunk.
            overlap: Overlap between chunks.

        Returns:
            List of text chunks.
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at a natural boundary (sentence, paragraph, word)
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind("\n\n", start, end)
                if para_break > start + chunk_size // 2:
                    end = para_break + 2
                else:
                    # Look for sentence break
                    for punct in [". ", "! ", "? ", "\n"]:
                        sent_break = text.rfind(punct, start, end)
                        if sent_break > start + chunk_size // 2:
                            end = sent_break + len(punct)
                            break
                    else:
                        # Fall back to word boundary
                        space = text.rfind(" ", start, end)
                        if space > start + chunk_size // 2:
                            end = space + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - overlap if end < len(text) else len(text)

        return chunks


@lru_cache(maxsize=1)
def get_embedder(model_name: str = DEFAULT_MODEL) -> LocalEmbedder:
    """Get a cached embedder instance.

    Args:
        model_name: The model to use.

    Returns:
        LocalEmbedder instance.
    """
    return LocalEmbedder(model_name)


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector.
        vec2: Second vector.

    Returns:
        Cosine similarity score (-1 to 1).
    """
    if not HAS_NUMPY:
        # Pure Python fallback
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
