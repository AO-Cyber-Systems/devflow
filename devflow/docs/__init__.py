"""Dev Documentation management module.

Provides:
- Documentation models and CRUD operations
- Local embedding generation (FastEmbed) - optional
- SQLite-based vector store (sqlite-vec) - optional
- SQLite-based knowledge graph
- Integrated semantic search

Optional dependencies for semantic features:
- numpy: pip install numpy
- fastembed: pip install fastembed
- sqlite-vec: pip install sqlite-vec (optional, falls back to brute force)
"""

from .models import (
    DocFormat,
    DocType,
    Documentation,
)
from .manager import DocManager

# Core exports always available
__all__ = [
    # Models
    "DocFormat",
    "DocType",
    "Documentation",
    # Manager
    "DocManager",
]

# Optional semantic features (require numpy)
try:
    from .embedder import LocalEmbedder, get_embedder, cosine_similarity
    from .vector_store import VectorStore
    from .knowledge_graph import KnowledgeGraph, RelationType
    from .semantic_store import (
        SemanticStore,
        get_project_semantic_store,
        get_global_semantic_store,
    )

    __all__.extend([
        # Embeddings
        "LocalEmbedder",
        "get_embedder",
        "cosine_similarity",
        # Vector Store
        "VectorStore",
        # Knowledge Graph
        "KnowledgeGraph",
        "RelationType",
        # Semantic Store
        "SemanticStore",
        "get_project_semantic_store",
        "get_global_semantic_store",
    ])

    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
