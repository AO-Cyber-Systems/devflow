"""Integrated semantic store combining vector search and knowledge graph.

This module provides a unified interface for semantic document storage,
combining embedding-based similarity search with relationship-based
knowledge graph queries.

Enhanced with dual embedding support (Apple NLEmbedding + FastEmbed) and
AI-powered query expansion for improved search results.
"""

import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING

from .embedder import LocalEmbedder, get_embedder
from .knowledge_graph import KnowledgeGraph, RelationType
from .vector_store import VectorStore

if TYPE_CHECKING:
    from devflow.ai.embeddings import DualEmbedder

logger = logging.getLogger(__name__)


class SemanticStore:
    """Unified semantic storage for documentation.

    Combines:
    - Vector store for semantic similarity search
    - Knowledge graph for relationship queries
    - Dual embeddings (Apple NLEmbedding + FastEmbed) for best offline performance
    - AI-powered query expansion for improved search results
    """

    def __init__(
        self,
        base_path: str | Path,
        embedder: LocalEmbedder | None = None,
        use_dual_embedder: bool = True,
    ):
        """Initialize the semantic store.

        Args:
            base_path: Base path for the database files.
            embedder: Optional custom embedder (uses default if not provided).
            use_dual_embedder: Use dual embedding system (Apple + FastEmbed).
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Initialize embedder - try dual embedder first if requested
        self._dual_embedder: "DualEmbedder | None" = None
        if use_dual_embedder:
            try:
                from devflow.ai.embeddings import get_dual_embedder
                self._dual_embedder = get_dual_embedder()
                self.embedder = embedder or get_embedder()  # Keep for compatibility
                logger.info("Using dual embedder (Apple + FastEmbed)")
            except ImportError:
                logger.debug("Dual embedder not available, using FastEmbed only")
                self.embedder = embedder or get_embedder()
        else:
            self.embedder = embedder or get_embedder()

        # Use dimensions from the active embedder
        dimensions = (
            self._dual_embedder.dimensions if self._dual_embedder
            else self.embedder.dimensions
        )

        self.vector_store = VectorStore(
            db_path=self.base_path / "vectors.db",
            dimensions=dimensions,
        )
        self.knowledge_graph = KnowledgeGraph(
            db_path=self.base_path / "knowledge.db",
        )

        # AI provider for query expansion (lazy loaded)
        self._ai_provider = None

        logger.info(f"SemanticStore initialized at {self.base_path}")

    def index_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        doc_type: str,
        metadata: dict[str, Any] | None = None,
        related_docs: list[tuple[str, str]] | None = None,
        concepts: list[str] | None = None,
    ) -> dict:
        """Index a document for semantic search and knowledge graph.

        Args:
            doc_id: Unique document identifier.
            title: Document title.
            content: Document content.
            doc_type: Type of document (api, guide, etc.).
            metadata: Optional metadata to store.
            related_docs: List of (doc_id, relationship_type) tuples.
            concepts: List of concepts this document defines or uses.

        Returns:
            Indexing results with chunk count and graph updates.
        """
        results = {
            "doc_id": doc_id,
            "chunks_indexed": 0,
            "node_created": False,
            "edges_created": 0,
            "concepts_linked": 0,
        }

        # 1. Embed and store document chunks
        try:
            chunks = self._embed_document(
                content=content,
                title=title,
                description=metadata.get("description") if metadata else None,
            )

            chunk_metadata = {
                **(metadata or {}),
                "title": title,
                "doc_type": doc_type,
            }

            self.vector_store.add_document(
                doc_id=doc_id,
                chunks=chunks,
                metadata=chunk_metadata,
            )
            results["chunks_indexed"] = len(chunks)
        except Exception as e:
            logger.error(f"Error indexing document vectors: {e}")

        # 2. Add document to knowledge graph
        try:
            node_data = {
                "title": title,
                "doc_type": doc_type,
                **(metadata or {}),
            }
            self.knowledge_graph.add_node(
                node_id=doc_id,
                node_type="document",
                label=title,
                data=node_data,
            )
            results["node_created"] = True
        except Exception as e:
            logger.error(f"Error adding document to graph: {e}")

        # 3. Add relationships to other documents
        if related_docs:
            for related_id, rel_type in related_docs:
                try:
                    self.knowledge_graph.add_edge(
                        source_id=doc_id,
                        target_id=related_id,
                        relationship_type=rel_type,
                    )
                    results["edges_created"] += 1
                except Exception as e:
                    logger.error(f"Error adding relationship: {e}")

        # 4. Link to concepts
        if concepts:
            for concept in concepts:
                try:
                    concept_id = f"concept:{concept.lower().replace(' ', '_')}"

                    # Ensure concept node exists
                    self.knowledge_graph.add_node(
                        node_id=concept_id,
                        node_type="concept",
                        label=concept,
                    )

                    # Link document to concept
                    self.knowledge_graph.add_edge(
                        source_id=doc_id,
                        target_id=concept_id,
                        relationship_type=RelationType.DEFINES.value,
                    )
                    results["concepts_linked"] += 1
                except Exception as e:
                    logger.error(f"Error linking concept: {e}")

        return results

    def remove_document(self, doc_id: str) -> dict:
        """Remove a document from both stores.

        Args:
            doc_id: Document identifier.

        Returns:
            Removal results.
        """
        results = {
            "doc_id": doc_id,
            "chunks_removed": 0,
            "node_removed": False,
        }

        # Remove from vector store
        chunks_removed = self.vector_store.remove_document(doc_id)
        results["chunks_removed"] = chunks_removed

        # Remove from knowledge graph
        node_removed = self.knowledge_graph.remove_node(doc_id)
        results["node_removed"] = node_removed

        return results

    def _get_ai_provider(self):
        """Get or create AI provider for query expansion."""
        if self._ai_provider is None:
            try:
                from devflow.ai import get_ai_provider
                self._ai_provider = get_ai_provider()
            except ImportError:
                logger.debug("AI provider not available for query expansion")
        return self._ai_provider

    def _embed_text(self, text: str) -> list[float]:
        """Embed text using the best available embedder."""
        if self._dual_embedder:
            return self._dual_embedder.embed(text)
        return self.embedder.embed_text(text)

    def _embed_document(
        self,
        content: str,
        title: str | None = None,
        description: str | None = None,
    ) -> list[tuple[str, list[float]]]:
        """Embed document using the best available embedder."""
        if self._dual_embedder:
            # Use the standard embedder for document chunking
            return self.embedder.embed_document(content, title, description)
        return self.embedder.embed_document(content, title, description)

    async def _expand_query_async(self, query: str, context: str = "") -> str:
        """Expand query using AI (async version)."""
        provider = self._get_ai_provider()
        if provider and provider.is_available:
            try:
                return await provider.expand_query(query, context)
            except Exception as e:
                logger.debug(f"Query expansion failed: {e}")
        return query

    def expand_query(self, query: str, context: str = "") -> str:
        """Expand query using AI to improve search results.

        Args:
            query: Original search query.
            context: Optional context for expansion.

        Returns:
            Expanded query with related terms.
        """
        import asyncio

        provider = self._get_ai_provider()
        if provider and provider.is_available:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            try:
                return loop.run_until_complete(
                    self._expand_query_async(query, context)
                )
            except Exception as e:
                logger.debug(f"Query expansion failed: {e}")

        return query

    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        doc_ids: list[str] | None = None,
        include_related: bool = True,
        relationship_types: list[str] | None = None,
        expand_query: bool = False,
    ) -> list[dict]:
        """Search documents using semantic similarity and graph relationships.

        Args:
            query: Search query text.
            limit: Maximum results.
            doc_ids: Optional filter to specific documents.
            include_related: Include related documents from graph.
            relationship_types: Filter relationships if including related.
            expand_query: Use AI to expand the query for better results.

        Returns:
            List of search results with similarity scores and relationships.
        """
        # Optionally expand query
        search_query = query
        if expand_query:
            search_query = self.expand_query(query)
            if search_query != query:
                logger.debug(f"Expanded query: '{query}' -> '{search_query}'")

        # 1. Embed query
        query_embedding = self._embed_text(search_query)

        # 2. Vector similarity search
        vector_results = self.vector_store.search(
            query_embedding=query_embedding,
            limit=limit,
            doc_ids=doc_ids,
        )

        # 3. Optionally enhance with graph relationships
        if include_related and vector_results:
            # Get unique doc IDs from results
            found_doc_ids = list({r["doc_id"] for r in vector_results})

            # Find related documents
            related_docs = set()
            for doc_id in found_doc_ids[:5]:  # Limit graph expansion
                edges = self.knowledge_graph.get_edges(
                    doc_id,
                    direction="both",
                    relationship_type=None,
                )
                for edge in edges:
                    if relationship_types and edge["relationship_type"] not in relationship_types:
                        continue
                    related_id = (
                        edge["target_id"]
                        if edge["direction"] == "outgoing"
                        else edge["source_id"]
                    )
                    if related_id not in found_doc_ids:
                        related_docs.add(related_id)

            # Add graph relationship info to results
            for result in vector_results:
                doc_id = result["doc_id"]
                edges = self.knowledge_graph.get_edges(doc_id, direction="both")
                result["relationships"] = [
                    {
                        "type": e["relationship_type"],
                        "direction": e["direction"],
                        "related_id": (
                            e["target_id"]
                            if e["direction"] == "outgoing"
                            else e["source_id"]
                        ),
                    }
                    for e in edges
                ]

        return vector_results

    def find_related(
        self,
        doc_id: str,
        relationship_types: list[str] | None = None,
        depth: int = 1,
    ) -> dict:
        """Find documents related to a given document via the knowledge graph.

        Args:
            doc_id: Document identifier.
            relationship_types: Optional filter for relationship types.
            depth: How many hops to traverse.

        Returns:
            Related documents and their relationships.
        """
        return self.knowledge_graph.get_neighbors(
            node_id=doc_id,
            depth=depth,
            relationship_types=relationship_types,
        )

    def get_document_context(
        self,
        doc_id: str,
        include_similar: bool = True,
        include_related: bool = True,
        similar_limit: int = 5,
    ) -> dict:
        """Get comprehensive context for a document.

        Combines vector similarity and graph relationships to provide
        full context around a document.

        Args:
            doc_id: Document identifier.
            include_similar: Include semantically similar chunks.
            include_related: Include graph-related documents.
            similar_limit: Max similar documents.

        Returns:
            Context dictionary with document info, similar, and related docs.
        """
        context = {
            "doc_id": doc_id,
            "node": None,
            "similar_documents": [],
            "related_documents": [],
            "concepts": [],
        }

        # Get document node info
        node = self.knowledge_graph.get_node(doc_id)
        if node:
            context["node"] = node

        # Find semantically similar documents
        if include_similar:
            chunks = self.vector_store.get_document_chunks(doc_id)
            if chunks:
                # Use first chunk as representative
                first_chunk = chunks[0]["chunk_text"]
                query_embedding = self._embed_text(first_chunk)

                similar = self.vector_store.search(
                    query_embedding=query_embedding,
                    limit=similar_limit + 1,  # +1 to exclude self
                )

                # Filter out self
                context["similar_documents"] = [
                    s for s in similar if s["doc_id"] != doc_id
                ][:similar_limit]

        # Find graph-related documents
        if include_related:
            related = self.knowledge_graph.get_related_documents(
                doc_id=doc_id,
                limit=20,
            )
            context["related_documents"] = related

            # Get linked concepts
            edges = self.knowledge_graph.get_edges(
                doc_id,
                direction="outgoing",
                relationship_type=RelationType.DEFINES.value,
            )
            for edge in edges:
                if edge["target_id"].startswith("concept:"):
                    concept_node = self.knowledge_graph.get_node(edge["target_id"])
                    if concept_node:
                        context["concepts"].append(concept_node["label"])

        return context

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str | RelationType,
        weight: float = 1.0,
        metadata: dict | None = None,
    ) -> bool:
        """Add a relationship between documents.

        Args:
            source_id: Source document ID.
            target_id: Target document ID.
            relationship_type: Type of relationship.
            weight: Relationship weight.
            metadata: Optional metadata.

        Returns:
            True if relationship was created.
        """
        return self.knowledge_graph.add_edge(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            weight=weight,
            data=metadata,
        )

    def remove_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str | RelationType | None = None,
    ) -> int:
        """Remove a relationship between documents.

        Args:
            source_id: Source document ID.
            target_id: Target document ID.
            relationship_type: Optional type filter.

        Returns:
            Number of relationships removed.
        """
        return self.knowledge_graph.remove_edge(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
        )

    def get_stats(self) -> dict:
        """Get combined statistics.

        Returns:
            Dictionary with stats from both stores.
        """
        stats = {
            "vector_store": self.vector_store.get_stats(),
            "knowledge_graph": self.knowledge_graph.get_stats(),
            "base_path": str(self.base_path),
        }

        # Add embedder info
        if self._dual_embedder:
            stats["embedder"] = self._dual_embedder.get_status()
        else:
            stats["embedder"] = {
                "type": "fastembed",
                "model": self.embedder.model_name,
                "dimensions": self.embedder.dimensions,
            }

        # Add AI availability
        provider = self._get_ai_provider()
        stats["ai_available"] = bool(provider and provider.is_available)

        return stats

    def close(self):
        """Close all database connections."""
        self.vector_store.close()
        self.knowledge_graph.close()


def get_project_semantic_store(project_path: str | Path) -> SemanticStore:
    """Get a semantic store for a specific project.

    Args:
        project_path: Path to the project.

    Returns:
        SemanticStore instance for the project.
    """
    store_path = Path(project_path) / ".devflow" / "semantic"
    return SemanticStore(base_path=store_path)


def get_global_semantic_store() -> SemanticStore:
    """Get the global semantic store.

    Returns:
        SemanticStore instance for global documents.
    """
    store_path = Path.home() / ".devflow" / "semantic"
    return SemanticStore(base_path=store_path)
