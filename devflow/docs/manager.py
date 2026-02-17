"""Documentation manager for CRUD operations.

Enhanced with AI capabilities:
- Auto-summarization of documents
- Auto-tagging with AI-generated tags
- Entity extraction
- Related document suggestions
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .models import DocFormat, DocType, Documentation

if TYPE_CHECKING:
    from .semantic_store import SemanticStore
    from devflow.ai.providers import AIProvider

logger = logging.getLogger(__name__)


class DocManager:
    """Manages documentation storage and retrieval.

    Integrates with semantic store for vector search and knowledge graph.
    """

    GLOBAL_DOCS_DIR = Path.home() / ".devflow" / "docs"
    PROJECT_DOCS_DIR = ".devflow/docs"
    INDEX_FILE = "index.json"

    def __init__(self, enable_semantic: bool = True, enable_ai: bool = True):
        """Initialize the document manager.

        Args:
            enable_semantic: Enable semantic indexing (vector store + knowledge graph).
            enable_ai: Enable AI-powered features (summarization, tagging, etc.).
        """
        self._enable_semantic = enable_semantic
        self._enable_ai = enable_ai
        self._semantic_stores: dict[str, "SemanticStore"] = {}
        self._ai_provider: "AIProvider | None" = None
        self._ensure_global_docs_dir()

    def _ensure_global_docs_dir(self):
        """Ensure the global docs directory exists."""
        self.GLOBAL_DOCS_DIR.mkdir(parents=True, exist_ok=True)
        index_file = self.GLOBAL_DOCS_DIR / self.INDEX_FILE
        if not index_file.exists():
            self._save_index(self.GLOBAL_DOCS_DIR, [])

    def _get_semantic_store(self, project_path: str | None) -> "SemanticStore | None":
        """Get the semantic store for a project or global.

        Args:
            project_path: Project path or None for global.

        Returns:
            SemanticStore instance or None if semantic is disabled.
        """
        if not self._enable_semantic:
            return None

        # Use project path as cache key, or "__global__" for global store
        cache_key = project_path or "__global__"

        if cache_key not in self._semantic_stores:
            try:
                from .semantic_store import (
                    get_project_semantic_store,
                    get_global_semantic_store,
                )

                if project_path:
                    self._semantic_stores[cache_key] = get_project_semantic_store(
                        project_path
                    )
                else:
                    self._semantic_stores[cache_key] = get_global_semantic_store()

                logger.info(f"Initialized semantic store for: {cache_key}")
            except ImportError as e:
                logger.warning(f"Semantic store not available: {e}")
                self._enable_semantic = False
                return None
            except Exception as e:
                logger.error(f"Error initializing semantic store: {e}")
                return None

        return self._semantic_stores.get(cache_key)

    def _get_ai_provider(self) -> "AIProvider | None":
        """Get or create AI provider instance.

        Returns:
            AIProvider instance or None if AI is disabled.
        """
        if not self._enable_ai:
            return None

        if self._ai_provider is None:
            try:
                from devflow.ai import get_ai_provider
                self._ai_provider = get_ai_provider()
                logger.info("AI provider initialized")
            except ImportError as e:
                logger.warning(f"AI provider not available: {e}")
                self._enable_ai = False
                return None
            except Exception as e:
                logger.error(f"Error initializing AI provider: {e}")
                return None

        return self._ai_provider

    def _run_async(self, coro):
        """Run async coroutine in event loop."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    def _index_document(self, doc: Documentation, project_path: str | None):
        """Index a document in the semantic store.

        Args:
            doc: Document to index.
            project_path: Project path or None for global.
        """
        store = self._get_semantic_store(project_path)
        if not store:
            return

        try:
            metadata = {
                "description": doc.description,
                "tags": doc.tags,
                "format": doc.format.value,
            }
            if doc.ai_context:
                metadata["ai_context"] = doc.ai_context

            # Extract concepts from tags (simple heuristic)
            concepts = doc.tags if doc.tags else None

            store.index_document(
                doc_id=doc.id,
                title=doc.title,
                content=doc.content,
                doc_type=doc.doc_type.value,
                metadata=metadata,
                concepts=concepts,
            )
            logger.debug(f"Indexed document: {doc.id}")
        except Exception as e:
            logger.error(f"Error indexing document {doc.id}: {e}")

    def _remove_from_index(self, doc_id: str, project_path: str | None):
        """Remove a document from the semantic store.

        Args:
            doc_id: Document ID.
            project_path: Project path or None for global.
        """
        store = self._get_semantic_store(project_path)
        if not store:
            return

        try:
            store.remove_document(doc_id)
            logger.debug(f"Removed document from semantic index: {doc_id}")
        except Exception as e:
            logger.error(f"Error removing document {doc_id} from index: {e}")

    def _get_docs_dir(self, project_path: str | None) -> Path:
        """Get the documentation directory for a project or global."""
        if project_path:
            return Path(project_path) / self.PROJECT_DOCS_DIR
        return self.GLOBAL_DOCS_DIR

    def _ensure_docs_dir(self, project_path: str | None):
        """Ensure the docs directory exists for a project."""
        docs_dir = self._get_docs_dir(project_path)
        docs_dir.mkdir(parents=True, exist_ok=True)
        index_file = docs_dir / self.INDEX_FILE
        if not index_file.exists():
            self._save_index(docs_dir, [])

    def _load_index(self, docs_dir: Path) -> list[dict]:
        """Load the index file."""
        index_file = docs_dir / self.INDEX_FILE
        if not index_file.exists():
            return []
        try:
            return json.loads(index_file.read_text())
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading docs index: {e}")
            return []

    def _save_index(self, docs_dir: Path, index: list[dict]):
        """Save the index file."""
        index_file = docs_dir / self.INDEX_FILE
        index_file.write_text(json.dumps(index, indent=2))

    def _get_doc_filename(self, doc: Documentation) -> str:
        """Generate a filename for a documentation."""
        # Use ID for uniqueness with a readable prefix
        safe_title = "".join(c if c.isalnum() else "_" for c in doc.title[:30])
        return f"{safe_title}_{doc.id[:8]}{doc.format.file_extension}"

    def list_docs(
        self,
        project_path: str | None = None,
        doc_type: str | None = None,
        search: str | None = None,
    ) -> list[Documentation]:
        """List documentation with optional filters.

        Args:
            project_path: Project path for project-specific docs, None for global
            doc_type: Filter by document type
            search: Search in title and description

        Returns:
            List of Documentation objects (without content for performance).
        """
        docs_dir = self._get_docs_dir(project_path)
        if not docs_dir.exists():
            return []

        index = self._load_index(docs_dir)
        docs = []

        for entry in index:
            try:
                # Load just metadata, not content
                doc = Documentation.from_dict(entry)

                # Apply filters
                if doc_type and doc.doc_type.value != doc_type:
                    continue

                if search:
                    search_lower = search.lower()
                    if (
                        search_lower not in doc.title.lower()
                        and search_lower not in doc.description.lower()
                        and not any(search_lower in tag.lower() for tag in doc.tags)
                    ):
                        continue

                docs.append(doc)
            except Exception as e:
                logger.error(f"Error loading doc entry: {e}")
                continue

        return docs

    def get_doc(self, doc_id: str, project_path: str | None = None) -> Documentation | None:
        """Get a single documentation by ID with full content.

        Args:
            doc_id: Document ID
            project_path: Project path or None for global

        Returns:
            Documentation with content, or None if not found.
        """
        docs_dir = self._get_docs_dir(project_path)
        if not docs_dir.exists():
            return None

        index = self._load_index(docs_dir)

        for entry in index:
            if entry.get("id") == doc_id:
                # Load the full content from file
                content_file = entry.get("_content_file")
                if content_file:
                    content_path = docs_dir / content_file
                    if content_path.exists():
                        entry["content"] = content_path.read_text()

                return Documentation.from_dict(entry)

        return None

    def create_doc(
        self,
        title: str,
        content: str,
        doc_type: str,
        format: str,
        project_path: str | None = None,
        description: str = "",
        tags: list[str] | None = None,
        ai_context: str | None = None,
        auto_summarize: bool = False,
        auto_tag: bool = False,
    ) -> Documentation:
        """Create a new documentation.

        Args:
            title: Document title
            content: Document content
            doc_type: Document type (api, architecture, etc.)
            format: Content format (markdown, json, etc.)
            project_path: Project path or None for global
            description: Optional description
            tags: Optional tags
            ai_context: Optional AI context hints
            auto_summarize: Use AI to generate summary for ai_context
            auto_tag: Use AI to generate tags

        Returns:
            Created Documentation object.
        """
        self._ensure_docs_dir(project_path)
        docs_dir = self._get_docs_dir(project_path)

        # AI-powered enhancements
        final_ai_context = ai_context
        final_tags = tags or []

        if auto_summarize and not ai_context:
            provider = self._get_ai_provider()
            if provider and provider.is_available:
                try:
                    result = self._run_async(provider.summarize(content, max_length=300))
                    final_ai_context = result.summary
                    logger.info(f"Auto-generated summary for: {title}")
                except Exception as e:
                    logger.warning(f"Auto-summarize failed: {e}")

        if auto_tag:
            provider = self._get_ai_provider()
            if provider and provider.is_available:
                try:
                    ai_tags = self._run_async(provider.generate_tags(content, max_tags=10))
                    # Merge with provided tags
                    existing = set(final_tags)
                    existing.update(ai_tags)
                    final_tags = list(existing)
                    logger.info(f"Auto-generated {len(ai_tags)} tags for: {title}")
                except Exception as e:
                    logger.warning(f"Auto-tag failed: {e}")

        doc = Documentation.create(
            title=title,
            doc_type=DocType(doc_type),
            format=DocFormat(format),
            content=content,
            project_id=project_path,
            description=description,
            tags=final_tags,
            ai_context=final_ai_context,
        )

        # Save content to file
        filename = self._get_doc_filename(doc)
        content_path = docs_dir / filename
        content_path.write_text(content)

        # Update index
        index = self._load_index(docs_dir)
        entry = doc.to_dict(include_content=False)
        entry["_content_file"] = filename
        index.append(entry)
        self._save_index(docs_dir, index)

        # Index in semantic store
        self._index_document(doc, project_path)

        return doc

    def update_doc(
        self,
        doc_id: str,
        project_path: str | None = None,
        title: str | None = None,
        content: str | None = None,
        doc_type: str | None = None,
        format: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        ai_context: str | None = None,
    ) -> Documentation | None:
        """Update an existing documentation.

        Args:
            doc_id: Document ID
            project_path: Project path or None for global
            title: New title (optional)
            content: New content (optional)
            doc_type: New type (optional)
            format: New format (optional)
            description: New description (optional)
            tags: New tags (optional)
            ai_context: New AI context (optional)

        Returns:
            Updated Documentation, or None if not found.
        """
        docs_dir = self._get_docs_dir(project_path)
        if not docs_dir.exists():
            return None

        index = self._load_index(docs_dir)

        for i, entry in enumerate(index):
            if entry.get("id") == doc_id:
                # Update fields
                if title is not None:
                    entry["title"] = title
                if doc_type is not None:
                    entry["doc_type"] = doc_type
                if format is not None:
                    entry["format"] = format
                if description is not None:
                    entry["description"] = description
                if tags is not None:
                    entry["tags"] = tags
                if ai_context is not None:
                    entry["ai_context"] = ai_context

                entry["updated_at"] = datetime.now().isoformat()

                # Update content file if content changed
                if content is not None:
                    content_file = entry.get("_content_file")
                    if content_file:
                        content_path = docs_dir / content_file
                        content_path.write_text(content)
                    entry["content"] = content

                # Save index
                index[i] = entry
                self._save_index(docs_dir, index)

                # Re-index in semantic store if content changed
                doc = Documentation.from_dict(entry)
                if content is not None:
                    self._index_document(doc, project_path)

                return doc

        return None

    def delete_doc(self, doc_id: str, project_path: str | None = None) -> bool:
        """Delete a documentation.

        Args:
            doc_id: Document ID
            project_path: Project path or None for global

        Returns:
            True if deleted, False if not found.
        """
        docs_dir = self._get_docs_dir(project_path)
        if not docs_dir.exists():
            return False

        index = self._load_index(docs_dir)

        for i, entry in enumerate(index):
            if entry.get("id") == doc_id:
                # Delete content file
                content_file = entry.get("_content_file")
                if content_file:
                    content_path = docs_dir / content_file
                    if content_path.exists():
                        content_path.unlink()

                # Remove from index
                del index[i]
                self._save_index(docs_dir, index)

                # Remove from semantic store
                self._remove_from_index(doc_id, project_path)

                return True

        return False

    def import_from_file(
        self,
        file_path: str,
        project_path: str | None = None,
        doc_type: str = "custom",
        ai_context: str | None = None,
    ) -> Documentation:
        """Import documentation from a file.

        Args:
            file_path: Path to the file to import
            project_path: Project path or None for global
            doc_type: Document type
            ai_context: Optional AI context hints

        Returns:
            Created Documentation object.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = path.read_text()
        title = path.stem.replace("_", " ").replace("-", " ").title()

        # Detect format from extension
        ext = path.suffix.lower()
        format_map = {
            ".md": DocFormat.MARKDOWN,
            ".markdown": DocFormat.MARKDOWN,
            ".json": DocFormat.JSON,
            ".yaml": DocFormat.YAML,
            ".yml": DocFormat.YAML,
            ".txt": DocFormat.PLAINTEXT,
        }
        doc_format = format_map.get(ext, DocFormat.PLAINTEXT)

        # Check for OpenAPI/AsyncAPI
        if ext in (".json", ".yaml", ".yml"):
            content_lower = content.lower()
            if "openapi" in content_lower:
                doc_format = DocFormat.OPENAPI
            elif "asyncapi" in content_lower:
                doc_format = DocFormat.ASYNCAPI

        doc = self.create_doc(
            title=title,
            content=content,
            doc_type=doc_type,
            format=doc_format.value,
            project_path=project_path,
            ai_context=ai_context,
        )
        doc.source_file = str(path)

        return doc

    def get_ai_context(
        self,
        project_path: str | None = None,
        doc_types: list[str] | None = None,
    ) -> str:
        """Get aggregated AI context from all matching documentation.

        This generates a single context string suitable for providing to AI tools.

        Args:
            project_path: Project path or None for global
            doc_types: Filter by document types

        Returns:
            Aggregated AI context string.
        """
        docs = self.list_docs(project_path=project_path)

        if doc_types:
            docs = [d for d in docs if d.doc_type.value in doc_types]

        if not docs:
            return ""

        # Load full content for each doc
        full_docs = []
        for doc in docs:
            full_doc = self.get_doc(doc.id, project_path)
            if full_doc:
                full_docs.append(full_doc)

        # Generate combined context
        parts = ["# Project Documentation\n"]

        for doc in full_docs:
            parts.append(doc.to_ai_context())
            parts.append("\n---\n")

        return "\n".join(parts)

    # -------------------------------------------------------------------------
    # Semantic Search Methods
    # -------------------------------------------------------------------------

    def semantic_search(
        self,
        query: str,
        project_path: str | None = None,
        limit: int = 10,
        include_related: bool = True,
    ) -> list[dict]:
        """Search documents using semantic similarity.

        Args:
            query: Search query text.
            project_path: Project path or None for global.
            limit: Maximum results.
            include_related: Include graph-related documents.

        Returns:
            List of search results with similarity scores.
        """
        store = self._get_semantic_store(project_path)

        # Try semantic search if available
        if store:
            try:
                results = store.semantic_search(
                    query=query,
                    limit=limit,
                    include_related=include_related,
                )
                if results:
                    # Enrich with document metadata
                    enriched = []
                    for result in results:
                        doc = self.get_doc(result["doc_id"], project_path)
                        if doc:
                            enriched.append(
                                {
                                    **result,
                                    "title": doc.title,
                                    "doc_type": doc.doc_type.value,
                                    "description": doc.description,
                                    "tags": doc.tags,
                                }
                            )
                        else:
                            enriched.append(result)
                    return enriched
            except Exception as e:
                logger.warning(f"Semantic search failed, falling back to text search: {e}")

        # Fall back to text search
        docs = self.list_docs(project_path=project_path, search=query)
        return [
            {
                "doc_id": doc.id,
                "title": doc.title,
                "doc_type": doc.doc_type.value,
                "description": doc.description,
                "similarity": 1.0,
                "chunk_text": doc.description or doc.title,
                "tags": doc.tags,
                "fallback": True,
            }
            for doc in docs[:limit]
        ]

    def get_related_docs(
        self,
        doc_id: str,
        project_path: str | None = None,
        relationship_types: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Get documents related to a given document via knowledge graph.

        Args:
            doc_id: Document identifier.
            project_path: Project path or None for global.
            relationship_types: Optional filter for relationship types.
            limit: Maximum results.

        Returns:
            List of related documents with relationship info.
        """
        store = self._get_semantic_store(project_path)
        if not store:
            return []

        related = store.knowledge_graph.get_related_documents(
            doc_id=doc_id,
            relationship_types=relationship_types,
            limit=limit,
        )

        # Enrich with full document info
        enriched = []
        for item in related:
            doc = self.get_doc(item["id"], project_path)
            if doc:
                enriched.append(
                    {
                        "doc_id": doc.id,
                        "title": doc.title,
                        "doc_type": doc.doc_type.value,
                        "description": doc.description,
                        "relationships": item.get("relationships", []),
                    }
                )

        return enriched

    def add_relationship(
        self,
        source_doc_id: str,
        target_doc_id: str,
        relationship_type: str,
        project_path: str | None = None,
    ) -> bool:
        """Add a relationship between two documents.

        Args:
            source_doc_id: Source document ID.
            target_doc_id: Target document ID.
            relationship_type: Type of relationship.
            project_path: Project path or None for global.

        Returns:
            True if relationship was created.
        """
        store = self._get_semantic_store(project_path)
        if not store:
            return False

        return store.add_relationship(
            source_id=source_doc_id,
            target_id=target_doc_id,
            relationship_type=relationship_type,
        )

    def remove_relationship(
        self,
        source_doc_id: str,
        target_doc_id: str,
        relationship_type: str | None = None,
        project_path: str | None = None,
    ) -> int:
        """Remove a relationship between documents.

        Args:
            source_doc_id: Source document ID.
            target_doc_id: Target document ID.
            relationship_type: Optional type filter.
            project_path: Project path or None for global.

        Returns:
            Number of relationships removed.
        """
        store = self._get_semantic_store(project_path)
        if not store:
            return 0

        return store.remove_relationship(
            source_id=source_doc_id,
            target_id=target_doc_id,
            relationship_type=relationship_type,
        )

    def get_semantic_stats(self, project_path: str | None = None) -> dict | None:
        """Get semantic store statistics.

        Args:
            project_path: Project path or None for global.

        Returns:
            Statistics dictionary or None if semantic is disabled.
        """
        store = self._get_semantic_store(project_path)
        if not store:
            return None

        return store.get_stats()

    def reindex_all(self, project_path: str | None = None) -> dict:
        """Reindex all documents in the semantic store.

        Useful after enabling semantic indexing or if the index becomes corrupted.

        Args:
            project_path: Project path or None for global.

        Returns:
            Reindexing results.
        """
        results = {
            "indexed": 0,
            "failed": 0,
            "total": 0,
        }

        docs = self.list_docs(project_path=project_path)
        results["total"] = len(docs)

        for doc in docs:
            full_doc = self.get_doc(doc.id, project_path)
            if full_doc:
                try:
                    self._index_document(full_doc, project_path)
                    results["indexed"] += 1
                except Exception as e:
                    logger.error(f"Error reindexing {doc.id}: {e}")
                    results["failed"] += 1

        return results

    # -------------------------------------------------------------------------
    # AI-Powered Methods
    # -------------------------------------------------------------------------

    def summarize_doc(
        self,
        doc_id: str,
        project_path: str | None = None,
        max_length: int = 500,
    ) -> dict[str, Any]:
        """Generate AI summary for a document.

        Args:
            doc_id: Document ID.
            project_path: Project path or None for global.
            max_length: Maximum summary length.

        Returns:
            Summary result with title, key_points, and summary.
        """
        doc = self.get_doc(doc_id, project_path)
        if not doc:
            return {"error": f"Document not found: {doc_id}"}

        provider = self._get_ai_provider()
        if not provider or not provider.is_available:
            return {"error": "AI provider not available"}

        try:
            result = self._run_async(provider.summarize(doc.content, max_length))
            return {
                "doc_id": doc_id,
                "title": result.title,
                "key_points": result.key_points,
                "summary": result.summary,
            }
        except Exception as e:
            logger.error(f"Summarize doc failed: {e}")
            return {"error": str(e)}

    def extract_doc_entities(
        self,
        doc_id: str,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """Extract entities from a document using AI.

        Args:
            doc_id: Document ID.
            project_path: Project path or None for global.

        Returns:
            Extracted entities: APIs, components, concepts, suggested_tags.
        """
        doc = self.get_doc(doc_id, project_path)
        if not doc:
            return {"error": f"Document not found: {doc_id}"}

        provider = self._get_ai_provider()
        if not provider or not provider.is_available:
            return {"error": "AI provider not available"}

        try:
            result = self._run_async(provider.extract_entities(doc.content))
            return {
                "doc_id": doc_id,
                "apis": result.apis,
                "components": result.components,
                "concepts": result.concepts,
                "suggested_tags": result.suggested_tags,
            }
        except Exception as e:
            logger.error(f"Extract entities failed: {e}")
            return {"error": str(e)}

    def suggest_related_docs(
        self,
        doc_id: str,
        project_path: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """Suggest related documents using AI and semantic similarity.

        Combines semantic search with knowledge graph relationships to
        find the most relevant related documents.

        Args:
            doc_id: Document ID.
            project_path: Project path or None for global.
            limit: Maximum number of suggestions.

        Returns:
            List of related document suggestions with relevance info.
        """
        doc = self.get_doc(doc_id, project_path)
        if not doc:
            return []

        suggestions = []
        seen_ids = {doc_id}

        # 1. Get semantically similar documents
        store = self._get_semantic_store(project_path)
        if store:
            try:
                # Use document content as query
                similar = store.semantic_search(
                    query=doc.content[:2000],  # Limit query length
                    limit=limit + 1,
                    include_related=False,
                )
                for result in similar:
                    if result["doc_id"] not in seen_ids:
                        seen_ids.add(result["doc_id"])
                        suggestions.append({
                            "doc_id": result["doc_id"],
                            "title": result.get("title", ""),
                            "similarity": result.get("similarity", 0),
                            "source": "semantic",
                        })
            except Exception as e:
                logger.debug(f"Semantic search for suggestions failed: {e}")

        # 2. Get graph-related documents
        related = self.get_related_docs(doc_id, project_path, limit=limit)
        for rel in related:
            if rel["doc_id"] not in seen_ids:
                seen_ids.add(rel["doc_id"])
                suggestions.append({
                    "doc_id": rel["doc_id"],
                    "title": rel.get("title", ""),
                    "similarity": 0.8,  # Fixed score for graph relations
                    "source": "graph",
                    "relationships": rel.get("relationships", []),
                })

        # Sort by similarity and limit
        suggestions.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return suggestions[:limit]

    def validate_doc_quality(
        self,
        doc_id: str,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """Validate document quality using AI.

        Args:
            doc_id: Document ID.
            project_path: Project path or None for global.

        Returns:
            Quality scores and improvement suggestions.
        """
        doc = self.get_doc(doc_id, project_path)
        if not doc:
            return {"error": f"Document not found: {doc_id}"}

        provider = self._get_ai_provider()
        if not provider or not provider.is_available:
            return {"error": "AI provider not available"}

        # Use the prompt template directly
        from devflow.ai.prompts import PromptTemplates

        try:
            prompt = PromptTemplates.format_validate_quality(
                title=doc.title,
                doc_type=doc.doc_type.display_name,
                content=doc.content,
            )
            result = self._run_async(provider.complete(prompt, max_tokens=500))

            if not result.success:
                return {"error": result.error or "AI request failed"}

            # Parse the response (basic parsing)
            return {
                "doc_id": doc_id,
                "analysis": result.content,
                "raw_response": True,  # Indicates unparsed response
            }
        except Exception as e:
            logger.error(f"Validate doc quality failed: {e}")
            return {"error": str(e)}

    def auto_enhance_doc(
        self,
        doc_id: str,
        project_path: str | None = None,
        generate_summary: bool = True,
        generate_tags: bool = True,
    ) -> Documentation | None:
        """Auto-enhance a document with AI-generated summary and tags.

        Args:
            doc_id: Document ID.
            project_path: Project path or None for global.
            generate_summary: Generate AI summary for ai_context.
            generate_tags: Generate AI tags.

        Returns:
            Updated Documentation or None if not found.
        """
        doc = self.get_doc(doc_id, project_path)
        if not doc:
            return None

        provider = self._get_ai_provider()
        if not provider or not provider.is_available:
            logger.warning("AI provider not available for auto-enhance")
            return doc

        updates: dict[str, Any] = {}

        # Generate summary
        if generate_summary:
            try:
                result = self._run_async(provider.summarize(doc.content, max_length=300))
                updates["ai_context"] = result.summary
                logger.info(f"Generated summary for doc: {doc_id}")
            except Exception as e:
                logger.warning(f"Summary generation failed: {e}")

        # Generate tags
        if generate_tags:
            try:
                ai_tags = self._run_async(provider.generate_tags(doc.content, max_tags=10))
                # Merge with existing tags
                existing_tags = set(doc.tags or [])
                existing_tags.update(ai_tags)
                updates["tags"] = list(existing_tags)
                logger.info(f"Generated {len(ai_tags)} tags for doc: {doc_id}")
            except Exception as e:
                logger.warning(f"Tag generation failed: {e}")

        # Apply updates
        if updates:
            return self.update_doc(doc_id, project_path, **updates)

        return doc

    def get_ai_status(self) -> dict[str, Any]:
        """Get AI availability status.

        Returns:
            Dictionary with AI availability information.
        """
        provider = self._get_ai_provider()
        if not provider:
            return {
                "enabled": self._enable_ai,
                "available": False,
                "provider": None,
            }

        return {
            "enabled": self._enable_ai,
            "available": provider.is_available,
            "provider": provider.name,
        }
