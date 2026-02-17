"""RPC handler for dev documentation management."""

import logging
from typing import Any

from devflow.docs.manager import DocManager

logger = logging.getLogger(__name__)


class DocsHandler:
    """Handler for managing dev documentation."""

    def __init__(self):
        self._manager: DocManager | None = None

    def _get_manager(self) -> DocManager:
        """Get or create the doc manager instance."""
        if self._manager is None:
            self._manager = DocManager()
        return self._manager

    def list_docs(
        self,
        project_path: str | None = None,
        doc_type: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """List documentation with optional filters.

        Args:
            project_path: Project path for project-specific docs, None for global
            doc_type: Filter by document type (api, architecture, etc.)
            search: Search in title, description, and tags

        Returns:
            Dictionary with docs list.
        """
        try:
            manager = self._get_manager()
            docs = manager.list_docs(
                project_path=project_path,
                doc_type=doc_type,
                search=search,
            )
            return {
                "docs": [d.to_dict(include_content=False) for d in docs],
                "total": len(docs),
            }
        except Exception as e:
            logger.error(f"List docs failed: {e}")
            return {"error": str(e)}

    def get_doc(
        self,
        doc_id: str,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """Get a single documentation by ID with full content.

        Args:
            doc_id: Document ID
            project_path: Project path or None for global

        Returns:
            Documentation details or error.
        """
        try:
            manager = self._get_manager()
            doc = manager.get_doc(doc_id, project_path)

            if doc is None:
                return {"error": f"Documentation not found: {doc_id}"}

            return {"doc": doc.to_dict(include_content=True)}
        except Exception as e:
            logger.error(f"Get doc failed: {e}")
            return {"error": str(e)}

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
    ) -> dict[str, Any]:
        """Create a new documentation.

        Args:
            title: Document title
            content: Document content
            doc_type: Document type (api, architecture, component, guide, reference, tutorial, custom)
            format: Content format (markdown, json, yaml, openapi, asyncapi, plaintext)
            project_path: Project path or None for global
            description: Optional description
            tags: Optional tags
            ai_context: Optional AI context hints
            auto_summarize: Use AI to generate summary for ai_context
            auto_tag: Use AI to generate tags

        Returns:
            Created documentation details.
        """
        try:
            manager = self._get_manager()
            doc = manager.create_doc(
                title=title,
                content=content,
                doc_type=doc_type,
                format=format,
                project_path=project_path,
                description=description,
                tags=tags,
                ai_context=ai_context,
                auto_summarize=auto_summarize,
                auto_tag=auto_tag,
            )
            return {
                "success": True,
                "doc": doc.to_dict(include_content=True),
            }
        except Exception as e:
            logger.error(f"Create doc failed: {e}")
            return {"success": False, "error": str(e)}

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
    ) -> dict[str, Any]:
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
            Updated documentation details.
        """
        try:
            manager = self._get_manager()
            doc = manager.update_doc(
                doc_id=doc_id,
                project_path=project_path,
                title=title,
                content=content,
                doc_type=doc_type,
                format=format,
                description=description,
                tags=tags,
                ai_context=ai_context,
            )

            if doc is None:
                return {"success": False, "error": f"Documentation not found: {doc_id}"}

            return {
                "success": True,
                "doc": doc.to_dict(include_content=True),
            }
        except Exception as e:
            logger.error(f"Update doc failed: {e}")
            return {"success": False, "error": str(e)}

    def delete_doc(
        self,
        doc_id: str,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """Delete a documentation.

        Args:
            doc_id: Document ID
            project_path: Project path or None for global

        Returns:
            Deletion result.
        """
        try:
            manager = self._get_manager()
            deleted = manager.delete_doc(doc_id, project_path)

            if not deleted:
                return {"success": False, "error": f"Documentation not found: {doc_id}"}

            return {"success": True, "message": "Documentation deleted"}
        except Exception as e:
            logger.error(f"Delete doc failed: {e}")
            return {"success": False, "error": str(e)}

    def import_from_file(
        self,
        file_path: str,
        project_path: str | None = None,
        doc_type: str = "custom",
        ai_context: str | None = None,
    ) -> dict[str, Any]:
        """Import documentation from a file.

        Args:
            file_path: Path to the file to import
            project_path: Project path or None for global
            doc_type: Document type
            ai_context: Optional AI context hints

        Returns:
            Imported documentation details.
        """
        try:
            manager = self._get_manager()
            doc = manager.import_from_file(
                file_path=file_path,
                project_path=project_path,
                doc_type=doc_type,
                ai_context=ai_context,
            )
            return {
                "success": True,
                "doc": doc.to_dict(include_content=True),
            }
        except FileNotFoundError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Import doc failed: {e}")
            return {"success": False, "error": str(e)}

    def get_ai_context(
        self,
        project_path: str | None = None,
        doc_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get aggregated AI context from all matching documentation.

        This generates a single context string suitable for providing to AI tools.

        Args:
            project_path: Project path or None for global
            doc_types: Filter by document types

        Returns:
            Aggregated AI context string.
        """
        try:
            manager = self._get_manager()
            context = manager.get_ai_context(
                project_path=project_path,
                doc_types=doc_types,
            )
            return {
                "context": context,
                "length": len(context),
            }
        except Exception as e:
            logger.error(f"Get AI context failed: {e}")
            return {"error": str(e)}

    def get_doc_types(self) -> dict[str, Any]:
        """Get available document types.

        Returns:
            List of document types with display names and icons.
        """
        from devflow.docs.models import DocType

        return {
            "types": [
                {
                    "id": t.value,
                    "name": t.display_name,
                    "icon": t.icon,
                }
                for t in DocType
            ]
        }

    def get_doc_formats(self) -> dict[str, Any]:
        """Get available document formats.

        Returns:
            List of document formats with display names.
        """
        from devflow.docs.models import DocFormat

        return {
            "formats": [
                {
                    "id": f.value,
                    "name": f.display_name,
                    "extension": f.file_extension,
                }
                for f in DocFormat
            ]
        }

    # -------------------------------------------------------------------------
    # Semantic Search Methods
    # -------------------------------------------------------------------------

    def semantic_search(
        self,
        query: str,
        project_path: str | None = None,
        limit: int = 10,
        include_related: bool = True,
    ) -> dict[str, Any]:
        """Search documents using semantic similarity.

        Uses vector embeddings for semantic search and optionally
        includes related documents from the knowledge graph.

        Args:
            query: Search query text
            project_path: Project path or None for global
            limit: Maximum results
            include_related: Include graph-related documents

        Returns:
            List of search results with similarity scores.
        """
        try:
            manager = self._get_manager()
            results = manager.semantic_search(
                query=query,
                project_path=project_path,
                limit=limit,
                include_related=include_related,
            )
            return {
                "results": results,
                "total": len(results),
                "query": query,
            }
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return {"error": str(e), "results": []}

    def get_related_docs(
        self,
        doc_id: str,
        project_path: str | None = None,
        relationship_types: list[str] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Get documents related to a given document via knowledge graph.

        Args:
            doc_id: Document identifier
            project_path: Project path or None for global
            relationship_types: Optional filter for relationship types
            limit: Maximum results

        Returns:
            List of related documents with relationship info.
        """
        try:
            manager = self._get_manager()
            related = manager.get_related_docs(
                doc_id=doc_id,
                project_path=project_path,
                relationship_types=relationship_types,
                limit=limit,
            )
            return {
                "related": related,
                "total": len(related),
                "doc_id": doc_id,
            }
        except Exception as e:
            logger.error(f"Get related docs failed: {e}")
            return {"error": str(e), "related": []}

    def add_relationship(
        self,
        source_doc_id: str,
        target_doc_id: str,
        relationship_type: str,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """Add a relationship between two documents.

        Args:
            source_doc_id: Source document ID
            target_doc_id: Target document ID
            relationship_type: Type of relationship (references, depends_on, etc.)
            project_path: Project path or None for global

        Returns:
            Success status.
        """
        try:
            manager = self._get_manager()
            created = manager.add_relationship(
                source_doc_id=source_doc_id,
                target_doc_id=target_doc_id,
                relationship_type=relationship_type,
                project_path=project_path,
            )
            return {
                "success": True,
                "created": created,
                "source_doc_id": source_doc_id,
                "target_doc_id": target_doc_id,
                "relationship_type": relationship_type,
            }
        except Exception as e:
            logger.error(f"Add relationship failed: {e}")
            return {"success": False, "error": str(e)}

    def remove_relationship(
        self,
        source_doc_id: str,
        target_doc_id: str,
        relationship_type: str | None = None,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """Remove a relationship between documents.

        Args:
            source_doc_id: Source document ID
            target_doc_id: Target document ID
            relationship_type: Optional type filter
            project_path: Project path or None for global

        Returns:
            Number of relationships removed.
        """
        try:
            manager = self._get_manager()
            removed = manager.remove_relationship(
                source_doc_id=source_doc_id,
                target_doc_id=target_doc_id,
                relationship_type=relationship_type,
                project_path=project_path,
            )
            return {
                "success": True,
                "removed": removed,
            }
        except Exception as e:
            logger.error(f"Remove relationship failed: {e}")
            return {"success": False, "error": str(e)}

    def get_relationship_types(self) -> dict[str, Any]:
        """Get available relationship types.

        Returns:
            List of relationship types.
        """
        from devflow.docs.knowledge_graph import RelationType

        return {
            "types": [
                {
                    "id": t.value,
                    "name": t.value.replace("_", " ").title(),
                }
                for t in RelationType
            ]
        }

    def get_semantic_stats(
        self,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """Get semantic store statistics.

        Args:
            project_path: Project path or None for global

        Returns:
            Statistics dictionary.
        """
        try:
            manager = self._get_manager()
            stats = manager.get_semantic_stats(project_path)
            if stats is None:
                return {
                    "enabled": False,
                    "message": "Semantic indexing is not available",
                }
            return {
                "enabled": True,
                **stats,
            }
        except Exception as e:
            logger.error(f"Get semantic stats failed: {e}")
            return {"error": str(e)}

    def reindex_all(
        self,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """Reindex all documents in the semantic store.

        Useful after enabling semantic indexing or to repair corrupted index.

        Args:
            project_path: Project path or None for global

        Returns:
            Reindexing results.
        """
        try:
            manager = self._get_manager()
            results = manager.reindex_all(project_path)
            return {
                "success": True,
                **results,
            }
        except Exception as e:
            logger.error(f"Reindex failed: {e}")
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------------------
    # Web Fetch Methods
    # -------------------------------------------------------------------------

    def fetch_url(
        self,
        url: str,
        max_pages: int = 1,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Fetch content from a URL.

        Args:
            url: URL to fetch
            max_pages: Maximum pages (1 for single page)
            timeout: Request timeout in seconds

        Returns:
            Fetched page content.
        """
        try:
            from devflow.docs.web_fetcher import get_web_fetcher

            fetcher = get_web_fetcher(max_pages=max_pages, timeout=timeout)
            result = fetcher.fetch_url(url)

            return {
                "success": result.success,
                "pages": [p.to_dict() for p in result.pages],
                "errors": result.errors,
                "total_fetched": result.total_fetched,
            }
        except Exception as e:
            logger.error(f"Fetch URL failed: {e}")
            return {"success": False, "error": str(e)}

    def fetch_docs_site(
        self,
        url: str,
        max_pages: int = 50,
        max_depth: int = 3,
        timeout: float = 30.0,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch an entire documentation site.

        Crawls the site following links up to max_depth, respecting
        include/exclude patterns.

        Args:
            url: Starting URL
            max_pages: Maximum pages to fetch
            max_depth: Maximum link depth to follow
            timeout: Request timeout in seconds
            include_patterns: URL patterns to include (regex)
            exclude_patterns: URL patterns to exclude (regex)

        Returns:
            All fetched pages.
        """
        try:
            from devflow.docs.web_fetcher import get_web_fetcher

            fetcher = get_web_fetcher(
                max_pages=max_pages,
                max_depth=max_depth,
                timeout=timeout,
            )
            result = fetcher.fetch_docs_site(
                url=url,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
            )

            return {
                "success": result.success,
                "pages": [p.to_dict() for p in result.pages],
                "errors": result.errors[:10],  # Limit errors in response
                "total_fetched": result.total_fetched,
            }
        except Exception as e:
            logger.error(f"Fetch docs site failed: {e}")
            return {"success": False, "error": str(e)}

    def import_from_url(
        self,
        url: str,
        project_path: str | None = None,
        doc_type: str = "reference",
        ai_context: str | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        """Fetch a URL and import it as a document.

        Combines fetch_url and create_doc in one operation.

        Args:
            url: URL to fetch
            project_path: Project path or None for global
            doc_type: Document type
            ai_context: Optional AI context hints
            title: Optional title override (uses page title if not provided)

        Returns:
            Created documentation details.
        """
        try:
            from devflow.docs.web_fetcher import get_web_fetcher

            # Fetch the URL
            fetcher = get_web_fetcher(max_pages=1)
            result = fetcher.fetch_url(url)

            if not result.success or not result.pages:
                return {
                    "success": False,
                    "error": result.errors[0] if result.errors else "Failed to fetch URL",
                }

            page = result.pages[0]

            # Create the doc
            manager = self._get_manager()
            doc = manager.create_doc(
                title=title or page.title,
                content=page.content,
                doc_type=doc_type,
                format="markdown",
                project_path=project_path,
                description=f"Imported from {url}",
                tags=["imported", "web"],
                ai_context=ai_context,
            )

            return {
                "success": True,
                "doc": doc.to_dict(include_content=True),
                "source_url": url,
            }
        except Exception as e:
            logger.error(f"Import from URL failed: {e}")
            return {"success": False, "error": str(e)}

    def import_docs_site(
        self,
        url: str,
        project_path: str | None = None,
        doc_type: str = "reference",
        max_pages: int = 50,
        max_depth: int = 3,
        path_prefix: str | None = None,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch and import an entire documentation site.

        Crawls the site and creates a document for each page.

        Args:
            url: Starting URL
            project_path: Project path or None for global
            doc_type: Document type for all imported docs
            max_pages: Maximum pages to fetch
            max_depth: Maximum link depth to follow
            path_prefix: Only crawl URLs with this path prefix (e.g., "/docs/")
            include_patterns: URL patterns to include
            exclude_patterns: URL patterns to exclude

        Returns:
            Import results with created documents.
        """
        try:
            from devflow.docs.web_fetcher import get_web_fetcher
            from urllib.parse import urlparse

            # If path_prefix is set, add it as an include pattern
            effective_include = list(include_patterns) if include_patterns else []
            if path_prefix:
                # Add pattern to match URLs with this path prefix
                parsed = urlparse(url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                prefix_pattern = f"{base_url}{path_prefix}*"
                effective_include.append(prefix_pattern)

            # Fetch the site
            fetcher = get_web_fetcher(max_pages=max_pages, max_depth=max_depth)
            result = fetcher.fetch_docs_site(
                url=url,
                include_patterns=effective_include if effective_include else None,
                exclude_patterns=exclude_patterns,
            )

            if not result.success:
                return {
                    "success": False,
                    "error": result.errors[0] if result.errors else "Failed to fetch site",
                }

            # Get site name for tagging
            site_name = urlparse(url).netloc

            # Create docs for each page
            manager = self._get_manager()
            created_docs = []
            import_errors = []

            for page in result.pages:
                try:
                    doc = manager.create_doc(
                        title=page.title,
                        content=page.content,
                        doc_type=doc_type,
                        format="markdown",
                        project_path=project_path,
                        description=f"Imported from {page.url}",
                        tags=["imported", "web", site_name],
                    )
                    created_docs.append({
                        "id": doc.id,
                        "title": doc.title,
                        "source_url": page.url,
                    })
                except Exception as e:
                    import_errors.append(f"{page.url}: {str(e)}")

            return {
                "success": True,
                "total_fetched": result.total_fetched,
                "total_imported": len(created_docs),
                "docs": created_docs,
                "errors": import_errors[:10],  # Limit errors
                "source_url": url,
            }
        except Exception as e:
            logger.error(f"Import docs site failed: {e}")
            return {"success": False, "error": str(e)}

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
            doc_id: Document ID
            project_path: Project path or None for global
            max_length: Maximum summary length

        Returns:
            Summary result with title, key_points, and summary.
        """
        try:
            manager = self._get_manager()
            result = manager.summarize_doc(doc_id, project_path, max_length)
            if "error" in result:
                return {"success": False, "error": result["error"]}
            return {"success": True, **result}
        except Exception as e:
            logger.error(f"Summarize doc failed: {e}")
            return {"success": False, "error": str(e)}

    def extract_doc_entities(
        self,
        doc_id: str,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """Extract entities from a document using AI.

        Args:
            doc_id: Document ID
            project_path: Project path or None for global

        Returns:
            Extracted entities: APIs, components, concepts, suggested_tags.
        """
        try:
            manager = self._get_manager()
            result = manager.extract_doc_entities(doc_id, project_path)
            if "error" in result:
                return {"success": False, "error": result["error"]}
            return {"success": True, **result}
        except Exception as e:
            logger.error(f"Extract doc entities failed: {e}")
            return {"success": False, "error": str(e)}

    def suggest_related_docs(
        self,
        doc_id: str,
        project_path: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Suggest related documents using AI and semantic similarity.

        Args:
            doc_id: Document ID
            project_path: Project path or None for global
            limit: Maximum number of suggestions

        Returns:
            List of related document suggestions.
        """
        try:
            manager = self._get_manager()
            suggestions = manager.suggest_related_docs(doc_id, project_path, limit)
            return {
                "success": True,
                "doc_id": doc_id,
                "suggestions": suggestions,
                "total": len(suggestions),
            }
        except Exception as e:
            logger.error(f"Suggest related docs failed: {e}")
            return {"success": False, "error": str(e)}

    def auto_enhance_doc(
        self,
        doc_id: str,
        project_path: str | None = None,
        generate_summary: bool = True,
        generate_tags: bool = True,
    ) -> dict[str, Any]:
        """Auto-enhance a document with AI-generated summary and tags.

        Args:
            doc_id: Document ID
            project_path: Project path or None for global
            generate_summary: Generate AI summary for ai_context
            generate_tags: Generate AI tags

        Returns:
            Enhanced document details.
        """
        try:
            manager = self._get_manager()
            doc = manager.auto_enhance_doc(
                doc_id=doc_id,
                project_path=project_path,
                generate_summary=generate_summary,
                generate_tags=generate_tags,
            )
            if doc is None:
                return {"success": False, "error": f"Document not found: {doc_id}"}
            return {
                "success": True,
                "doc": doc.to_dict(include_content=False),
            }
        except Exception as e:
            logger.error(f"Auto enhance doc failed: {e}")
            return {"success": False, "error": str(e)}

    def validate_doc_quality(
        self,
        doc_id: str,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """Validate document quality using AI.

        Args:
            doc_id: Document ID
            project_path: Project path or None for global

        Returns:
            Quality scores and improvement suggestions.
        """
        try:
            manager = self._get_manager()
            result = manager.validate_doc_quality(doc_id, project_path)
            if "error" in result:
                return {"success": False, "error": result["error"]}
            return {"success": True, **result}
        except Exception as e:
            logger.error(f"Validate doc quality failed: {e}")
            return {"success": False, "error": str(e)}

    def get_ai_status(self) -> dict[str, Any]:
        """Get AI availability status for docs.

        Returns:
            Dictionary with AI availability information.
        """
        try:
            manager = self._get_manager()
            return manager.get_ai_status()
        except Exception as e:
            logger.error(f"Get AI status failed: {e}")
            return {"enabled": False, "available": False, "error": str(e)}
