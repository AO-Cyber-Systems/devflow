"""
Code manager for indexing and searching code entities.

Integrates with SemanticStore for vector embeddings and
KnowledgeGraph for relationship storage.

Enhanced with AI capabilities:
- Code explanation and understanding
- Docstring generation
- Improvement suggestions
- Similar code search
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, TYPE_CHECKING

from .models import (
    ClassEntity,
    CodeEntity,
    CodeEntityType,
    CodeRelationType,
    FunctionEntity,
    ModuleEntity,
)
from .scanner import CodeScanner, ScanConfig, ScanResult
from .resolver import RelationshipResolver, ResolutionResult
from .chunker import SemanticChunker, CodeChunk

if TYPE_CHECKING:
    from devflow.ai.providers import AIProvider

logger = logging.getLogger(__name__)


@dataclass
class IndexResult:
    """Result of indexing operation."""

    project_path: str
    entities_indexed: int
    chunks_indexed: int
    relationships_indexed: int
    errors: list[str]
    duration_ms: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_path": self.project_path,
            "entities_indexed": self.entities_indexed,
            "chunks_indexed": self.chunks_indexed,
            "relationships_indexed": self.relationships_indexed,
            "errors": self.errors[:10],
            "duration_ms": self.duration_ms,
        }


@dataclass
class SearchResult:
    """A single search result."""

    entity: CodeEntity
    score: float
    chunk_type: str
    highlights: list[str] = field(default_factory=list)

    def to_dict(self, include_source: bool = False) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "entity": self.entity.to_dict(include_source=include_source),
            "score": self.score,
            "chunk_type": self.chunk_type,
            "highlights": self.highlights,
        }
        return result


class CodeManager:
    """Manages code indexing, storage, and search."""

    INDEX_FILE = "code_index.json"
    ENTITIES_FILE = "entities.json"
    CODE_DIR = ".devflow/code"

    def __init__(
        self,
        project_path: str | Path | None = None,
        enable_semantic: bool = True,
        enable_ai: bool = True,
    ):
        """
        Initialize the code manager.

        Args:
            project_path: Project root directory (None for global)
            enable_semantic: Enable semantic search features
            enable_ai: Enable AI-powered features
        """
        self._project_path = Path(project_path) if project_path else None
        self._enable_semantic = enable_semantic
        self._enable_ai = enable_ai
        self._semantic_store: Any | None = None
        self._ai_provider: "AIProvider | None" = None
        self._entities: dict[str, CodeEntity] = {}
        self._scan_result: ScanResult | None = None
        self._resolution_result: ResolutionResult | None = None

        # Ensure code directory exists
        self._ensure_code_dir()

    def _ensure_code_dir(self) -> None:
        """Ensure the code storage directory exists."""
        code_dir = self._get_code_dir()
        code_dir.mkdir(parents=True, exist_ok=True)

    def _get_code_dir(self) -> Path:
        """Get the code storage directory."""
        if self._project_path:
            return self._project_path / self.CODE_DIR
        return Path.home() / ".devflow" / "code"

    def _get_semantic_store(self) -> Any | None:
        """Get or create the semantic store."""
        if not self._enable_semantic:
            return None

        if self._semantic_store is None:
            try:
                from devflow.docs.semantic_store import get_project_semantic_store

                self._semantic_store = get_project_semantic_store(
                    str(self._project_path) if self._project_path else None
                )
            except Exception as e:
                logger.warning(f"Failed to initialize semantic store: {e}")
                return None

        return self._semantic_store

    def _get_ai_provider(self) -> "AIProvider | None":
        """Get or create AI provider instance."""
        if not self._enable_ai:
            return None

        if self._ai_provider is None:
            try:
                from devflow.ai import get_ai_provider
                self._ai_provider = get_ai_provider()
                logger.info("AI provider initialized for code analysis")
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

    def scan_project(
        self,
        languages: list[str] | None = None,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> ScanResult:
        """
        Scan the project for code entities.

        Args:
            languages: Languages to scan (None = all supported)
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            progress_callback: Callback for progress updates

        Returns:
            ScanResult with discovered entities
        """
        if not self._project_path:
            raise ValueError("No project path configured")

        config = ScanConfig(
            languages=languages or [],
            include_patterns=include_patterns or ScanConfig().include_patterns,
            exclude_patterns=exclude_patterns or [],
        )

        scanner = CodeScanner(self._project_path, config)

        if progress_callback:
            scanner.set_progress_callback(progress_callback)

        self._scan_result = scanner.scan()

        # Build entity map
        self._entities = {e.id: e for e in self._scan_result.entities}

        # Resolve relationships
        resolver = RelationshipResolver(self._scan_result.entities)
        self._resolution_result = resolver.resolve()

        logger.info(
            f"Scanned {self._scan_result.files_scanned} files, "
            f"found {len(self._entities)} entities, "
            f"{len(self._resolution_result.relationships)} relationships"
        )

        return self._scan_result

    def index_project(
        self,
        languages: list[str] | None = None,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> IndexResult:
        """
        Scan and index the project into the semantic store.

        Args:
            languages: Languages to scan
            progress_callback: Callback for progress updates

        Returns:
            IndexResult with indexing statistics
        """
        start_time = datetime.now()
        errors: list[str] = []

        # Scan if not already done
        if not self._scan_result:
            self.scan_project(languages=languages, progress_callback=progress_callback)

        if not self._scan_result:
            return IndexResult(
                project_path=str(self._project_path),
                entities_indexed=0,
                chunks_indexed=0,
                relationships_indexed=0,
                errors=["Scan failed"],
                duration_ms=0,
            )

        # Create chunks
        resolver = RelationshipResolver(self._scan_result.entities)
        chunker = SemanticChunker(self._scan_result.entities, resolver)
        chunks = chunker.create_chunks()

        # Index into semantic store
        store = self._get_semantic_store()
        chunks_indexed = 0
        entities_indexed = 0
        relationships_indexed = 0

        if store:
            # Index chunks
            for chunk in chunks:
                try:
                    # Create a document-like entry for the chunk
                    doc_id = f"code:{chunk.entity_id}:{chunk.chunk_type}"

                    store.index_document(
                        doc_id=doc_id,
                        title=chunk.metadata.get("name", ""),
                        content=chunk.content,
                        doc_type="code",
                        metadata=chunk.metadata,
                    )
                    chunks_indexed += 1

                except Exception as e:
                    errors.append(f"Chunk indexing error: {e}")

            # Index entities as nodes
            for entity in self._scan_result.entities:
                try:
                    store.knowledge_graph.add_node(
                        node_id=f"code:{entity.id}",
                        node_type=f"code_{entity.entity_type.value}",
                        label=entity.qualified_name,
                        data={
                            "name": entity.name,
                            "file": entity.file_path,
                            "line": entity.line_start,
                            "language": entity.language,
                            "tags": entity.tags,
                        },
                    )
                    entities_indexed += 1

                except Exception as e:
                    errors.append(f"Entity indexing error: {e}")

            # Index relationships
            if self._resolution_result:
                for rel in self._resolution_result.relationships:
                    try:
                        store.knowledge_graph.add_edge(
                            source_id=f"code:{rel.source_id}",
                            target_id=f"code:{rel.target_id}",
                            relationship_type=rel.relationship_type.value,
                            weight=rel.weight,
                            data=rel.metadata,
                        )
                        relationships_indexed += 1

                    except Exception as e:
                        errors.append(f"Relationship indexing error: {e}")

        # Save index metadata
        self._save_index_metadata()

        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        return IndexResult(
            project_path=str(self._project_path),
            entities_indexed=entities_indexed,
            chunks_indexed=chunks_indexed,
            relationships_indexed=relationships_indexed,
            errors=errors,
            duration_ms=duration_ms,
        )

    def _save_index_metadata(self) -> None:
        """Save index metadata and entities to file."""
        if not self._scan_result:
            return

        code_dir = self._get_code_dir()
        index_file = code_dir / self.INDEX_FILE
        entities_file = code_dir / self.ENTITIES_FILE

        metadata = {
            "project_path": str(self._project_path),
            "indexed_at": datetime.now().isoformat(),
            "scan_result": self._scan_result.to_dict(),
            "resolution_result": self._resolution_result.to_dict()
            if self._resolution_result
            else None,
            "entity_count": len(self._entities),
        }

        try:
            index_file.write_text(json.dumps(metadata, indent=2))
        except Exception as e:
            logger.error(f"Failed to save index metadata: {e}")

        # Save entities separately for quick loading
        try:
            entities_data = [
                {
                    "id": e.id,
                    "name": e.name,
                    "qualified_name": e.qualified_name,
                    "entity_type": e.entity_type.value,
                    "file_path": e.file_path,
                    "line_start": e.line_start,
                    "line_end": e.line_end,
                    "language": e.language,
                    "docstring": e.docstring,
                    "tags": e.tags,
                }
                for e in self._entities.values()
            ]
            entities_file.write_text(json.dumps(entities_data))
        except Exception as e:
            logger.error(f"Failed to save entities: {e}")

    def _load_index_metadata(self) -> dict[str, Any] | None:
        """Load index metadata from file."""
        code_dir = self._get_code_dir()
        index_file = code_dir / self.INDEX_FILE

        if not index_file.exists():
            return None

        try:
            return json.loads(index_file.read_text())
        except Exception as e:
            logger.error(f"Failed to load index metadata: {e}")
            return None

    def _load_entities(self) -> None:
        """Load entities from file if available."""
        code_dir = self._get_code_dir()
        entities_file = code_dir / self.ENTITIES_FILE

        if not entities_file.exists():
            return

        try:
            entities_data = json.loads(entities_file.read_text())
            for e in entities_data:
                entity = CodeEntity(
                    id=e["id"],
                    name=e["name"],
                    qualified_name=e["qualified_name"],
                    entity_type=CodeEntityType(e["entity_type"]),
                    file_path=e["file_path"],
                    line_start=e["line_start"],
                    line_end=e["line_end"],
                    language=e["language"],
                    docstring=e.get("docstring"),
                    source_code=None,  # Not persisted
                    tags=e.get("tags", []),
                )
                self._entities[entity.id] = entity
            logger.info(f"Loaded {len(self._entities)} entities from cache")
        except Exception as e:
            logger.error(f"Failed to load entities: {e}")

    def list_entities(
        self,
        entity_types: list[str] | None = None,
        language: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List indexed entities without semantic search.

        Args:
            entity_types: Filter by entity types
            language: Filter by language
            limit: Maximum results
            offset: Skip first N results

        Returns:
            List of entity dictionaries
        """
        # Load entities if not in memory
        if not self._entities:
            self._load_entities()

        results = []
        for entity in self._entities.values():
            # Apply filters
            if entity_types:
                if entity.entity_type.value not in entity_types:
                    continue
            if language:
                if entity.language != language:
                    continue

            results.append({
                "entity_id": entity.id,
                "name": entity.name,
                "qualified_name": entity.qualified_name,
                "entity_type": entity.entity_type.value,
                "file_path": entity.file_path,
                "line_start": entity.line_start,
                "language": entity.language,
                "docstring": entity.docstring,
            })

        # Sort by name
        results.sort(key=lambda x: x["name"].lower())

        # Apply pagination
        return results[offset:offset + limit]

    def search_code(
        self,
        query: str,
        entity_types: list[str] | None = None,
        language: str | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        """
        Search for code entities using semantic search.

        Args:
            query: Search query
            entity_types: Filter by entity types
            language: Filter by language
            limit: Maximum results

        Returns:
            List of SearchResult objects
        """
        store = self._get_semantic_store()
        results: list[SearchResult] = []

        if store:
            try:
                # Semantic search
                search_results = store.semantic_search(
                    query=query,
                    limit=limit * 2,  # Over-fetch for filtering
                    include_related=False,
                )

                for sr in search_results:
                    # Filter for code documents
                    if not sr.get("doc_id", "").startswith("code:"):
                        continue

                    # Parse entity info from metadata
                    metadata = sr.get("metadata", {})

                    # Apply filters
                    if entity_types:
                        if metadata.get("entity_type") not in entity_types:
                            continue

                    if language:
                        if metadata.get("language") != language:
                            continue

                    # Get the actual entity
                    entity_id = metadata.get("entity_id")
                    entity = self._entities.get(entity_id)

                    if entity:
                        results.append(
                            SearchResult(
                                entity=entity,
                                score=sr.get("score", 0.0),
                                chunk_type=metadata.get("chunk_type", "unknown"),
                            )
                        )

                    if len(results) >= limit:
                        break

            except Exception as e:
                logger.error(f"Semantic search failed: {e}")

        # Fallback to text search if no results
        if not results and self._entities:
            query_lower = query.lower()
            for entity in self._entities.values():
                if query_lower in entity.name.lower():
                    results.append(
                        SearchResult(
                            entity=entity,
                            score=1.0,
                            chunk_type="name_match",
                        )
                    )
                elif entity.docstring and query_lower in entity.docstring.lower():
                    results.append(
                        SearchResult(
                            entity=entity,
                            score=0.8,
                            chunk_type="docstring_match",
                        )
                    )

                if len(results) >= limit:
                    break

        return results[:limit]

    def find_function(self, name: str) -> list[FunctionEntity]:
        """
        Find functions by name.

        Args:
            name: Function name (partial match)

        Returns:
            List of matching FunctionEntity objects
        """
        results: list[FunctionEntity] = []
        name_lower = name.lower()

        for entity in self._entities.values():
            if entity.entity_type in (CodeEntityType.FUNCTION, CodeEntityType.METHOD):
                if isinstance(entity, FunctionEntity):
                    if name_lower in entity.name.lower():
                        results.append(entity)
                    elif name_lower in entity.qualified_name.lower():
                        results.append(entity)

        return results

    def find_class(self, name: str) -> list[ClassEntity]:
        """
        Find classes by name.

        Args:
            name: Class name (partial match)

        Returns:
            List of matching ClassEntity objects
        """
        results: list[ClassEntity] = []
        name_lower = name.lower()

        for entity in self._entities.values():
            if entity.entity_type == CodeEntityType.CLASS:
                if isinstance(entity, ClassEntity):
                    if name_lower in entity.name.lower():
                        results.append(entity)
                    elif name_lower in entity.qualified_name.lower():
                        results.append(entity)

        return results

    def get_entity(self, entity_id: str) -> CodeEntity | None:
        """Get an entity by ID."""
        return self._entities.get(entity_id)

    def get_entity_by_qualified_name(self, qualified_name: str) -> CodeEntity | None:
        """Get an entity by qualified name."""
        for entity in self._entities.values():
            if entity.qualified_name == qualified_name:
                return entity
        return None

    def get_callers(self, entity_id: str) -> list[CodeEntity]:
        """
        Get all entities that call the given entity.

        Args:
            entity_id: ID of the target entity

        Returns:
            List of calling entities
        """
        if not self._resolution_result:
            return []

        callers: list[CodeEntity] = []

        for rel in self._resolution_result.relationships:
            if rel.relationship_type == CodeRelationType.CALLS:
                if rel.target_id == entity_id:
                    caller = self._entities.get(rel.source_id)
                    if caller:
                        callers.append(caller)

        return callers

    def get_callees(self, entity_id: str) -> list[CodeEntity]:
        """
        Get all entities called by the given entity.

        Args:
            entity_id: ID of the calling entity

        Returns:
            List of called entities
        """
        if not self._resolution_result:
            return []

        callees: list[CodeEntity] = []

        for rel in self._resolution_result.relationships:
            if rel.relationship_type == CodeRelationType.CALLS:
                if rel.source_id == entity_id:
                    callee = self._entities.get(rel.target_id)
                    if callee:
                        callees.append(callee)

        return callees

    def get_dependencies(self, entity_id: str) -> dict[str, list[CodeEntity]]:
        """
        Get all dependencies of an entity.

        Args:
            entity_id: ID of the entity

        Returns:
            Dictionary with keys: imports, calls, extends, uses
        """
        if not self._resolution_result:
            return {"imports": [], "calls": [], "extends": [], "uses": []}

        deps: dict[str, list[CodeEntity]] = {
            "imports": [],
            "calls": [],
            "extends": [],
            "uses": [],
        }

        for rel in self._resolution_result.relationships:
            if rel.source_id != entity_id:
                continue

            target = self._entities.get(rel.target_id)
            if not target:
                continue

            if rel.relationship_type == CodeRelationType.IMPORTS:
                deps["imports"].append(target)
            elif rel.relationship_type == CodeRelationType.CALLS:
                deps["calls"].append(target)
            elif rel.relationship_type == CodeRelationType.EXTENDS:
                deps["extends"].append(target)
            elif rel.relationship_type == CodeRelationType.USES:
                deps["uses"].append(target)

        return deps

    def get_dependents(self, entity_id: str) -> dict[str, list[CodeEntity]]:
        """
        Get all entities that depend on the given entity.

        Args:
            entity_id: ID of the entity

        Returns:
            Dictionary with keys: callers, subclasses, importers
        """
        if not self._resolution_result:
            return {"callers": [], "subclasses": [], "importers": []}

        deps: dict[str, list[CodeEntity]] = {
            "callers": [],
            "subclasses": [],
            "importers": [],
        }

        for rel in self._resolution_result.relationships:
            if rel.target_id != entity_id:
                continue

            source = self._entities.get(rel.source_id)
            if not source:
                continue

            if rel.relationship_type == CodeRelationType.CALLS:
                deps["callers"].append(source)
            elif rel.relationship_type == CodeRelationType.EXTENDS:
                deps["subclasses"].append(source)
            elif rel.relationship_type == CodeRelationType.IMPORTS:
                deps["importers"].append(source)

        return deps

    def get_code_stats(self) -> dict[str, Any]:
        """Get statistics about the indexed code."""
        stats = {
            "project_path": str(self._project_path),
            "entities": {
                "total": len(self._entities),
                "by_type": {},
                "by_language": {},
            },
            "relationships": {
                "total": 0,
                "by_type": {},
            },
            "scan": None,
        }

        # Count by type
        type_counts: dict[str, int] = {}
        lang_counts: dict[str, int] = {}

        for entity in self._entities.values():
            type_name = entity.entity_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

            lang_counts[entity.language] = lang_counts.get(entity.language, 0) + 1

        stats["entities"]["by_type"] = type_counts
        stats["entities"]["by_language"] = lang_counts

        # Relationship stats
        if self._resolution_result:
            rel_type_counts: dict[str, int] = {}
            for rel in self._resolution_result.relationships:
                rel_type = rel.relationship_type.value
                rel_type_counts[rel_type] = rel_type_counts.get(rel_type, 0) + 1

            stats["relationships"]["total"] = len(self._resolution_result.relationships)
            stats["relationships"]["by_type"] = rel_type_counts

        # Scan result
        if self._scan_result:
            stats["scan"] = self._scan_result.to_dict()

        return stats

    def reindex_project(self) -> IndexResult:
        """
        Clear and rebuild the index.

        Returns:
            IndexResult with reindexing statistics
        """
        # Clear existing data
        self._entities.clear()
        self._scan_result = None
        self._resolution_result = None

        # Clear semantic store entries (if available)
        store = self._get_semantic_store()
        if store:
            try:
                # Remove code-related entries from the store
                # This would require adding a method to SemanticStore
                # For now, we'll just re-index on top
                pass
            except Exception as e:
                logger.warning(f"Failed to clear existing index: {e}")

        # Re-index
        return self.index_project()

    def get_scan_status(self) -> dict[str, Any]:
        """Get the current scan/index status."""
        metadata = self._load_index_metadata()

        if metadata:
            return {
                "indexed": True,
                "indexed_at": metadata.get("indexed_at"),
                "entity_count": metadata.get("entity_count", 0),
                "scan_result": metadata.get("scan_result"),
            }

        return {
            "indexed": False,
            "indexed_at": None,
            "entity_count": 0,
            "scan_result": None,
        }

    # -------------------------------------------------------------------------
    # AI-Powered Methods
    # -------------------------------------------------------------------------

    def explain_entity(
        self,
        entity_id: str,
        detail_level: str = "basic",
    ) -> dict[str, Any]:
        """Generate natural language explanation of a code entity.

        Args:
            entity_id: ID of the entity to explain.
            detail_level: One of "brief", "basic", "detailed".

        Returns:
            Explanation result with summary, steps, parameters, etc.
        """
        entity = self.get_entity(entity_id)
        if not entity:
            return {"error": f"Entity not found: {entity_id}"}

        provider = self._get_ai_provider()
        if not provider or not provider.is_available:
            return {"error": "AI provider not available"}

        # Get source code
        source_code = entity.source_code
        if not source_code:
            return {"error": "No source code available for entity"}

        try:
            result = self._run_async(
                provider.explain_code(source_code, entity.language, detail_level)
            )
            return {
                "entity_id": entity_id,
                "entity_name": entity.qualified_name,
                "language": entity.language,
                "summary": result.summary,
                "algorithm_steps": result.algorithm_steps,
                "parameters": result.parameters,
                "returns": result.returns,
                "example": result.example,
            }
        except Exception as e:
            logger.error(f"Explain entity failed: {e}")
            return {"error": str(e)}

    def generate_docstring(
        self,
        entity_id: str,
    ) -> dict[str, Any]:
        """Auto-generate docstring for a code entity.

        Args:
            entity_id: ID of the entity.

        Returns:
            Generated docstring.
        """
        entity = self.get_entity(entity_id)
        if not entity:
            return {"error": f"Entity not found: {entity_id}"}

        provider = self._get_ai_provider()
        if not provider or not provider.is_available:
            return {"error": "AI provider not available"}

        source_code = entity.source_code
        if not source_code:
            return {"error": "No source code available for entity"}

        try:
            docstring = self._run_async(
                provider.generate_docstring(source_code, entity.language)
            )
            return {
                "entity_id": entity_id,
                "entity_name": entity.qualified_name,
                "docstring": docstring,
            }
        except Exception as e:
            logger.error(f"Generate docstring failed: {e}")
            return {"error": str(e)}

    def suggest_improvements(
        self,
        entity_id: str,
    ) -> dict[str, Any]:
        """AI-suggested refactoring and improvement opportunities.

        Args:
            entity_id: ID of the entity.

        Returns:
            List of improvement suggestions.
        """
        entity = self.get_entity(entity_id)
        if not entity:
            return {"error": f"Entity not found: {entity_id}"}

        provider = self._get_ai_provider()
        if not provider or not provider.is_available:
            return {"error": "AI provider not available"}

        source_code = entity.source_code
        if not source_code:
            return {"error": "No source code available for entity"}

        try:
            suggestions = self._run_async(
                provider.suggest_improvements(source_code, entity.language)
            )
            return {
                "entity_id": entity_id,
                "entity_name": entity.qualified_name,
                "suggestions": suggestions,
            }
        except Exception as e:
            logger.error(f"Suggest improvements failed: {e}")
            return {"error": str(e)}

    def find_similar_code(
        self,
        entity_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Find semantically similar code using embeddings.

        Args:
            entity_id: ID of the entity.
            limit: Maximum number of similar entities.

        Returns:
            List of similar entities with similarity scores.
        """
        entity = self.get_entity(entity_id)
        if not entity:
            return []

        source_code = entity.source_code
        if not source_code:
            return []

        store = self._get_semantic_store()
        if not store:
            return []

        try:
            # Search using the entity's source code as query
            results = store.semantic_search(
                query=source_code[:2000],  # Limit query length
                limit=limit + 1,  # +1 to exclude self
                include_related=False,
            )

            similar: list[dict[str, Any]] = []
            for result in results:
                doc_id = result.get("doc_id", "")
                if not doc_id.startswith("code:"):
                    continue

                # Extract entity ID from doc_id
                parts = doc_id.split(":")
                if len(parts) >= 2:
                    found_entity_id = parts[1]
                    if found_entity_id == entity_id:
                        continue  # Skip self

                    found_entity = self.get_entity(found_entity_id)
                    if found_entity:
                        similar.append({
                            "entity_id": found_entity_id,
                            "entity_name": found_entity.qualified_name,
                            "entity_type": found_entity.entity_type.value,
                            "file_path": found_entity.file_path,
                            "similarity": result.get("similarity", 0.0),
                        })

            return similar[:limit]
        except Exception as e:
            logger.error(f"Find similar code failed: {e}")
            return []

    def detect_language(
        self,
        code: str,
    ) -> dict[str, Any]:
        """Detect programming language of a code snippet.

        Args:
            code: Code snippet.

        Returns:
            Detected language.
        """
        provider = self._get_ai_provider()
        if not provider or not provider.is_available:
            return {"error": "AI provider not available"}

        try:
            language = self._run_async(provider.detect_language(code))
            return {
                "language": language,
            }
        except Exception as e:
            logger.error(f"Detect language failed: {e}")
            return {"error": str(e)}

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
