"""RPC handler for AI operations.

Provides AI-powered features using Apple's on-device models with fallback
to local LLMs and optional cloud APIs.
"""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AIHandler:
    """Handler for AI operations.

    Provides endpoints for:
    - Text summarization
    - Entity extraction
    - Code explanation
    - Tag generation
    - Query expansion
    - Embeddings (single and batch)
    - Language detection
    - OCR (text extraction from images/PDFs)
    - Translation
    - AI status/availability checking
    """

    def __init__(self):
        self._provider = None
        self._embedder = None
        self._loop = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop for async operations."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def _run_async(self, coro):
        """Run async coroutine in event loop."""
        loop = self._get_loop()
        return loop.run_until_complete(coro)

    def _get_provider(self):
        """Get or create AI provider instance."""
        if self._provider is None:
            from devflow.ai import get_ai_provider
            self._provider = get_ai_provider()
        return self._provider

    def _get_embedder(self):
        """Get or create dual embedder instance."""
        if self._embedder is None:
            from devflow.ai import get_dual_embedder
            self._embedder = get_dual_embedder()
        return self._embedder

    # =========================================================================
    # Status and Availability
    # =========================================================================

    def get_ai_status(self) -> dict[str, Any]:
        """Get AI availability status for all providers.

        Returns:
            Dictionary with status of each AI provider and embedding backend.
        """
        try:
            from devflow.ai import get_available_providers

            providers = get_available_providers()
            embedder = self._get_embedder()
            embedding_status = embedder.get_status()

            # Determine overall availability
            any_provider_available = any(providers.values())

            return {
                "available": any_provider_available,
                "providers": providers,
                "embeddings": embedding_status,
                "active_provider": self._get_provider().name if any_provider_available else None,
            }
        except Exception as e:
            logger.error(f"Get AI status failed: {e}")
            return {
                "available": False,
                "error": str(e),
            }

    # =========================================================================
    # Summarization
    # =========================================================================

    def summarize(
        self,
        content: str,
        max_length: int = 500,
    ) -> dict[str, Any]:
        """Summarize text content.

        Args:
            content: Content to summarize.
            max_length: Maximum summary length.

        Returns:
            Summary result with title, key points, and summary.
        """
        try:
            provider = self._get_provider()
            result = self._run_async(provider.summarize(content, max_length))

            return {
                "success": True,
                "title": result.title,
                "key_points": result.key_points,
                "summary": result.summary,
            }
        except Exception as e:
            logger.error(f"Summarize failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Entity Extraction
    # =========================================================================

    def extract_entities(
        self,
        content: str,
    ) -> dict[str, Any]:
        """Extract entities from content.

        Args:
            content: Content to analyze.

        Returns:
            Extracted entities: APIs, components, concepts, suggested tags.
        """
        try:
            provider = self._get_provider()
            result = self._run_async(provider.extract_entities(content))

            return {
                "success": True,
                "apis": result.apis,
                "components": result.components,
                "concepts": result.concepts,
                "suggested_tags": result.suggested_tags,
            }
        except Exception as e:
            logger.error(f"Extract entities failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Code Explanation
    # =========================================================================

    def explain_code(
        self,
        code: str,
        language: str,
        detail_level: str = "basic",
    ) -> dict[str, Any]:
        """Explain code.

        Args:
            code: Code to explain.
            language: Programming language.
            detail_level: One of "brief", "basic", "detailed".

        Returns:
            Code explanation with summary, steps, parameters, return value.
        """
        try:
            provider = self._get_provider()
            result = self._run_async(provider.explain_code(code, language, detail_level))

            return {
                "success": True,
                "summary": result.summary,
                "algorithm_steps": result.algorithm_steps,
                "parameters": result.parameters,
                "returns": result.returns,
                "example": result.example,
            }
        except Exception as e:
            logger.error(f"Explain code failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Tag Generation
    # =========================================================================

    def generate_tags(
        self,
        content: str,
        max_tags: int = 10,
    ) -> dict[str, Any]:
        """Generate tags for content.

        Args:
            content: Content to tag.
            max_tags: Maximum number of tags.

        Returns:
            List of generated tags.
        """
        try:
            provider = self._get_provider()
            tags = self._run_async(provider.generate_tags(content, max_tags))

            return {
                "success": True,
                "tags": tags,
            }
        except Exception as e:
            logger.error(f"Generate tags failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Query Expansion
    # =========================================================================

    def expand_query(
        self,
        query: str,
        context: str = "",
    ) -> dict[str, Any]:
        """Expand a search query with related terms.

        Args:
            query: Original search query.
            context: Optional context for expansion.

        Returns:
            Expanded query string.
        """
        try:
            provider = self._get_provider()
            expanded = self._run_async(provider.expand_query(query, context))

            return {
                "success": True,
                "original_query": query,
                "expanded_query": expanded,
            }
        except Exception as e:
            logger.error(f"Expand query failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Docstring Generation
    # =========================================================================

    def generate_docstring(
        self,
        code: str,
        language: str,
    ) -> dict[str, Any]:
        """Generate docstring for code.

        Args:
            code: Code to document.
            language: Programming language.

        Returns:
            Generated docstring.
        """
        try:
            provider = self._get_provider()
            docstring = self._run_async(provider.generate_docstring(code, language))

            return {
                "success": True,
                "docstring": docstring,
            }
        except Exception as e:
            logger.error(f"Generate docstring failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Code Improvement Suggestions
    # =========================================================================

    def suggest_improvements(
        self,
        code: str,
        language: str,
    ) -> dict[str, Any]:
        """Suggest code improvements.

        Args:
            code: Code to analyze.
            language: Programming language.

        Returns:
            List of improvement suggestions.
        """
        try:
            provider = self._get_provider()
            suggestions = self._run_async(provider.suggest_improvements(code, language))

            return {
                "success": True,
                "suggestions": suggestions,
            }
        except Exception as e:
            logger.error(f"Suggest improvements failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Embeddings
    # =========================================================================

    def get_embedding(
        self,
        text: str,
    ) -> dict[str, Any]:
        """Get embedding vector for text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.
        """
        try:
            embedder = self._get_embedder()
            embedding = embedder.embed(text)

            return {
                "success": True,
                "embedding": embedding,
                "dimensions": len(embedding),
                "backend": embedder.active_backend,
            }
        except Exception as e:
            logger.error(f"Get embedding failed: {e}")
            return {"success": False, "error": str(e)}

    def batch_embeddings(
        self,
        texts: list[str],
    ) -> dict[str, Any]:
        """Get embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        try:
            embedder = self._get_embedder()
            embeddings = embedder.embed_batch(texts)

            return {
                "success": True,
                "embeddings": embeddings,
                "count": len(embeddings),
                "dimensions": embedder.dimensions,
                "backend": embedder.active_backend,
            }
        except Exception as e:
            logger.error(f"Batch embeddings failed: {e}")
            return {"success": False, "error": str(e)}

    def find_similar(
        self,
        query: str,
        texts: list[str],
        limit: int = 5,
        min_similarity: float = 0.0,
    ) -> dict[str, Any]:
        """Find texts most similar to query.

        Args:
            query: Query text.
            texts: List of texts to search.
            limit: Maximum number of results.
            min_similarity: Minimum similarity threshold.

        Returns:
            List of similar texts with scores.
        """
        try:
            embedder = self._get_embedder()
            results = embedder.find_similar(query, texts, limit, min_similarity)

            return {
                "success": True,
                "results": [
                    {"index": idx, "text": text, "similarity": sim}
                    for idx, text, sim in results
                ],
                "backend": embedder.active_backend,
            }
        except Exception as e:
            logger.error(f"Find similar failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Language Detection
    # =========================================================================

    def detect_language(
        self,
        code: str,
    ) -> dict[str, Any]:
        """Detect programming language of code.

        Args:
            code: Code snippet.

        Returns:
            Detected language.
        """
        try:
            provider = self._get_provider()
            language = self._run_async(provider.detect_language(code))

            return {
                "success": True,
                "language": language,
            }
        except Exception as e:
            logger.error(f"Detect language failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Translation
    # =========================================================================

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> dict[str, Any]:
        """Translate text.

        Args:
            text: Text to translate.
            source_lang: Source language.
            target_lang: Target language.

        Returns:
            Translated text.
        """
        try:
            provider = self._get_provider()
            translated = self._run_async(provider.translate(text, source_lang, target_lang))

            return {
                "success": True,
                "original": text,
                "translated": translated,
                "source_lang": source_lang,
                "target_lang": target_lang,
            }
        except Exception as e:
            logger.error(f"Translate failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # OCR / Text Extraction
    # =========================================================================

    def extract_text_from_image(
        self,
        image_path: str,
    ) -> dict[str, Any]:
        """Extract text from an image using OCR.

        Note: This currently requires the Swift bridge to be connected
        for full Vision framework support. Falls back to basic extraction.

        Args:
            image_path: Path to the image file.

        Returns:
            Extracted text.
        """
        try:
            import os
            if not os.path.exists(image_path):
                return {"success": False, "error": f"File not found: {image_path}"}

            # For now, return a message indicating Vision is needed
            # This will be fully implemented via Swift bridge
            return {
                "success": False,
                "error": "OCR requires Swift bridge connection (not yet implemented)",
                "requires": "swift_bridge",
            }
        except Exception as e:
            logger.error(f"Extract text from image failed: {e}")
            return {"success": False, "error": str(e)}

    def extract_text_from_pdf(
        self,
        pdf_path: str,
    ) -> dict[str, Any]:
        """Extract text from a PDF file.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            List of extracted text per page.
        """
        try:
            import os
            if not os.path.exists(pdf_path):
                return {"success": False, "error": f"File not found: {pdf_path}"}

            # Try PyMuPDF (fitz) for PDF extraction
            try:
                import fitz

                doc = fitz.open(pdf_path)
                pages = []
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    pages.append({
                        "page": page_num + 1,
                        "text": text,
                    })
                doc.close()

                return {
                    "success": True,
                    "pages": pages,
                    "total_pages": len(pages),
                }
            except ImportError:
                return {
                    "success": False,
                    "error": "PyMuPDF not installed. Install with: pip install pymupdf",
                }
        except Exception as e:
            logger.error(f"Extract text from PDF failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Document AI Operations (integrated with docs)
    # =========================================================================

    def summarize_doc(
        self,
        doc_id: str,
        project_path: str | None = None,
        max_length: int = 500,
    ) -> dict[str, Any]:
        """Summarize a document by ID.

        Args:
            doc_id: Document ID.
            project_path: Project path or None for global.
            max_length: Maximum summary length.

        Returns:
            Summary result.
        """
        try:
            from devflow.docs.manager import DocManager

            manager = DocManager()
            doc = manager.get_doc(doc_id, project_path)

            if doc is None:
                return {"success": False, "error": f"Document not found: {doc_id}"}

            # Summarize the document content
            return self.summarize(doc.content, max_length)
        except Exception as e:
            logger.error(f"Summarize doc failed: {e}")
            return {"success": False, "error": str(e)}

    def extract_doc_entities(
        self,
        doc_id: str,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """Extract entities from a document by ID.

        Args:
            doc_id: Document ID.
            project_path: Project path or None for global.

        Returns:
            Extracted entities.
        """
        try:
            from devflow.docs.manager import DocManager

            manager = DocManager()
            doc = manager.get_doc(doc_id, project_path)

            if doc is None:
                return {"success": False, "error": f"Document not found: {doc_id}"}

            # Extract entities from document content
            return self.extract_entities(doc.content)
        except Exception as e:
            logger.error(f"Extract doc entities failed: {e}")
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
            doc_id: Document ID.
            project_path: Project path or None for global.
            generate_summary: Whether to generate a summary.
            generate_tags: Whether to generate tags.

        Returns:
            Enhanced document.
        """
        try:
            from devflow.docs.manager import DocManager

            manager = DocManager()
            doc = manager.get_doc(doc_id, project_path)

            if doc is None:
                return {"success": False, "error": f"Document not found: {doc_id}"}

            updates = {}

            # Generate summary
            if generate_summary:
                summary_result = self.summarize(doc.content, max_length=300)
                if summary_result.get("success"):
                    updates["ai_context"] = summary_result.get("summary", "")

            # Generate tags
            if generate_tags:
                tags_result = self.generate_tags(doc.content, max_tags=10)
                if tags_result.get("success"):
                    new_tags = tags_result.get("tags", [])
                    # Merge with existing tags
                    existing_tags = set(doc.tags or [])
                    existing_tags.update(new_tags)
                    updates["tags"] = list(existing_tags)

            # Update the document if we have changes
            if updates:
                updated_doc = manager.update_doc(doc_id, project_path, **updates)
                if updated_doc:
                    return {
                        "success": True,
                        "doc": updated_doc.to_dict(include_content=False),
                        "enhancements": list(updates.keys()),
                    }

            return {
                "success": True,
                "doc": doc.to_dict(include_content=False),
                "enhancements": [],
                "message": "No enhancements made",
            }
        except Exception as e:
            logger.error(f"Auto enhance doc failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Code AI Operations (integrated with code)
    # =========================================================================

    def explain_entity(
        self,
        entity_id: str,
        project_path: str,
        detail_level: str = "basic",
    ) -> dict[str, Any]:
        """Explain a code entity by ID.

        Args:
            entity_id: Code entity ID.
            project_path: Project path.
            detail_level: One of "brief", "basic", "detailed".

        Returns:
            Code explanation.
        """
        try:
            from devflow.code.manager import CodeManager

            manager = CodeManager()
            entity = manager.get_entity(entity_id, project_path)

            if entity is None:
                return {"success": False, "error": f"Entity not found: {entity_id}"}

            # Get the source code
            source_code = entity.source_code or ""
            language = entity.language or "unknown"

            # Explain the code
            return self.explain_code(source_code, language, detail_level)
        except Exception as e:
            logger.error(f"Explain entity failed: {e}")
            return {"success": False, "error": str(e)}

    def generate_entity_docstring(
        self,
        entity_id: str,
        project_path: str,
    ) -> dict[str, Any]:
        """Generate docstring for a code entity.

        Args:
            entity_id: Code entity ID.
            project_path: Project path.

        Returns:
            Generated docstring.
        """
        try:
            from devflow.code.manager import CodeManager

            manager = CodeManager()
            entity = manager.get_entity(entity_id, project_path)

            if entity is None:
                return {"success": False, "error": f"Entity not found: {entity_id}"}

            source_code = entity.source_code or ""
            language = entity.language or "python"

            return self.generate_docstring(source_code, language)
        except Exception as e:
            logger.error(f"Generate entity docstring failed: {e}")
            return {"success": False, "error": str(e)}

    def suggest_entity_improvements(
        self,
        entity_id: str,
        project_path: str,
    ) -> dict[str, Any]:
        """Suggest improvements for a code entity.

        Args:
            entity_id: Code entity ID.
            project_path: Project path.

        Returns:
            List of improvement suggestions.
        """
        try:
            from devflow.code.manager import CodeManager

            manager = CodeManager()
            entity = manager.get_entity(entity_id, project_path)

            if entity is None:
                return {"success": False, "error": f"Entity not found: {entity_id}"}

            source_code = entity.source_code or ""
            language = entity.language or "python"

            return self.suggest_improvements(source_code, language)
        except Exception as e:
            logger.error(f"Suggest entity improvements failed: {e}")
            return {"success": False, "error": str(e)}
