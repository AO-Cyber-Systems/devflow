"""
RPC handler for code scanning and search operations.

Provides JSON-RPC methods for:
- Scanning projects for code entities
- Searching code with semantic queries
- Finding functions and classes
- Querying call relationships
- Getting code statistics
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class CodeHandler:
    """Handler for code scanning and search operations."""

    def __init__(self):
        """Initialize the code handler."""
        self._managers: dict[str, Any] = {}

    def _get_manager(self, project_path: str | None = None) -> Any:
        """Get or create a CodeManager for the project."""
        from devflow.code.manager import CodeManager

        cache_key = project_path or "__global__"

        if cache_key not in self._managers:
            self._managers[cache_key] = CodeManager(
                project_path=project_path,
                enable_semantic=True,
            )

        return self._managers[cache_key]

    # =========================================================================
    # Scanning Methods
    # =========================================================================

    def scan_project(
        self,
        project_path: str,
        languages: list[str] | None = None,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Scan a project for code entities.

        Args:
            project_path: Path to the project root
            languages: Optional list of languages to scan
            include_patterns: Optional file patterns to include
            exclude_patterns: Optional file patterns to exclude

        Returns:
            Scan result with entity counts and statistics
        """
        try:
            manager = self._get_manager(project_path)
            result = manager.scan_project(
                languages=languages,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
            )
            return {
                "success": True,
                "result": result.to_dict(),
            }
        except Exception as e:
            logger.error(f"Scan project failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def scan_file(
        self,
        file_path: str,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Scan a single file for code entities.

        Args:
            file_path: Path to the file
            project_path: Optional project context

        Returns:
            List of entities found in the file
        """
        try:
            manager = self._get_manager(project_path)
            entities = manager.scan_file(file_path) if hasattr(manager, 'scan_file') else []

            # If manager doesn't have scan_file, use scanner directly
            if not entities:
                from devflow.code.scanner import CodeScanner

                scanner = CodeScanner(project_path or ".")
                entities = scanner.scan_file(file_path)

            return {
                "success": True,
                "entities": [e.to_dict(include_source=True) for e in entities],
                "count": len(entities),
            }
        except Exception as e:
            logger.error(f"Scan file failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def index_project(
        self,
        project_path: str,
        languages: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Scan and index a project into the semantic store.

        Args:
            project_path: Path to the project root
            languages: Optional list of languages to scan

        Returns:
            Index result with statistics
        """
        try:
            manager = self._get_manager(project_path)
            result = manager.index_project(languages=languages)
            return {
                "success": True,
                "result": result.to_dict(),
            }
        except Exception as e:
            logger.error(f"Index project failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_scan_status(
        self,
        project_path: str,
    ) -> dict[str, Any]:
        """
        Get the current scan/index status for a project.

        Args:
            project_path: Path to the project root

        Returns:
            Status information including last scan time
        """
        try:
            manager = self._get_manager(project_path)
            status = manager.get_scan_status()
            return {
                "success": True,
                "status": status,
            }
        except Exception as e:
            logger.error(f"Get scan status failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def list_entities(
        self,
        project_path: str,
        entity_types: list[str] | None = None,
        language: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List indexed entities without semantic search.

        Args:
            project_path: Path to the project root
            entity_types: Optional filter by entity types
            language: Optional filter by language
            limit: Maximum results to return
            offset: Skip first N results

        Returns:
            List of entities
        """
        try:
            manager = self._get_manager(project_path)
            entities = manager.list_entities(
                entity_types=entity_types,
                language=language,
                limit=limit,
                offset=offset,
            )
            return {
                "success": True,
                "entities": entities,
                "count": len(entities),
            }
        except Exception as e:
            logger.error(f"List entities failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # =========================================================================
    # Search Methods
    # =========================================================================

    def search_code(
        self,
        query: str,
        project_path: str,
        entity_types: list[str] | None = None,
        language: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for code using semantic search.

        Args:
            query: Search query
            project_path: Path to the project root
            entity_types: Optional filter by entity types
            language: Optional filter by language
            limit: Maximum results to return

        Returns:
            List of matching entities with scores
        """
        try:
            manager = self._get_manager(project_path)
            results = manager.search_code(
                query=query,
                entity_types=entity_types,
                language=language,
                limit=limit,
            )
            return {
                "success": True,
                "results": [r.to_dict(include_source=False) for r in results],
                "total": len(results),
                "query": query,
            }
        except Exception as e:
            logger.error(f"Search code failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
            }

    def find_function(
        self,
        name: str,
        project_path: str,
        include_source: bool = False,
    ) -> dict[str, Any]:
        """
        Find functions by name.

        Args:
            name: Function name (partial match)
            project_path: Path to the project root
            include_source: Whether to include source code

        Returns:
            List of matching functions
        """
        try:
            manager = self._get_manager(project_path)
            functions = manager.find_function(name)
            return {
                "success": True,
                "functions": [f.to_dict(include_source=include_source) for f in functions],
                "count": len(functions),
            }
        except Exception as e:
            logger.error(f"Find function failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def find_class(
        self,
        name: str,
        project_path: str,
        include_source: bool = False,
    ) -> dict[str, Any]:
        """
        Find classes by name.

        Args:
            name: Class name (partial match)
            project_path: Path to the project root
            include_source: Whether to include source code

        Returns:
            List of matching classes
        """
        try:
            manager = self._get_manager(project_path)
            classes = manager.find_class(name)
            return {
                "success": True,
                "classes": [c.to_dict(include_source=include_source) for c in classes],
                "count": len(classes),
            }
        except Exception as e:
            logger.error(f"Find class failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_entity(
        self,
        entity_id: str,
        project_path: str,
        include_source: bool = True,
    ) -> dict[str, Any]:
        """
        Get a specific entity by ID.

        Args:
            entity_id: Entity ID
            project_path: Path to the project root
            include_source: Whether to include source code

        Returns:
            Entity details
        """
        try:
            manager = self._get_manager(project_path)
            entity = manager.get_entity(entity_id)

            if entity:
                return {
                    "success": True,
                    "entity": entity.to_dict(include_source=include_source),
                }
            else:
                return {
                    "success": False,
                    "error": "Entity not found",
                }
        except Exception as e:
            logger.error(f"Get entity failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # =========================================================================
    # Relationship Methods
    # =========================================================================

    def get_callers(
        self,
        entity_id: str,
        project_path: str,
    ) -> dict[str, Any]:
        """
        Get all entities that call the given entity.

        Args:
            entity_id: ID of the target entity
            project_path: Path to the project root

        Returns:
            List of calling entities
        """
        try:
            manager = self._get_manager(project_path)
            callers = manager.get_callers(entity_id)
            return {
                "success": True,
                "callers": [c.to_dict(include_source=False) for c in callers],
                "count": len(callers),
            }
        except Exception as e:
            logger.error(f"Get callers failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_callees(
        self,
        entity_id: str,
        project_path: str,
    ) -> dict[str, Any]:
        """
        Get all entities called by the given entity.

        Args:
            entity_id: ID of the calling entity
            project_path: Path to the project root

        Returns:
            List of called entities
        """
        try:
            manager = self._get_manager(project_path)
            callees = manager.get_callees(entity_id)
            return {
                "success": True,
                "callees": [c.to_dict(include_source=False) for c in callees],
                "count": len(callees),
            }
        except Exception as e:
            logger.error(f"Get callees failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_dependencies(
        self,
        entity_id: str,
        project_path: str,
    ) -> dict[str, Any]:
        """
        Get all dependencies of an entity.

        Args:
            entity_id: ID of the entity
            project_path: Path to the project root

        Returns:
            Dictionary with imports, calls, extends, uses
        """
        try:
            manager = self._get_manager(project_path)
            deps = manager.get_dependencies(entity_id)
            return {
                "success": True,
                "dependencies": {
                    key: [e.to_dict(include_source=False) for e in entities]
                    for key, entities in deps.items()
                },
            }
        except Exception as e:
            logger.error(f"Get dependencies failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_dependents(
        self,
        entity_id: str,
        project_path: str,
    ) -> dict[str, Any]:
        """
        Get all entities that depend on the given entity.

        Args:
            entity_id: ID of the entity
            project_path: Path to the project root

        Returns:
            Dictionary with callers, subclasses, importers
        """
        try:
            manager = self._get_manager(project_path)
            deps = manager.get_dependents(entity_id)
            return {
                "success": True,
                "dependents": {
                    key: [e.to_dict(include_source=False) for e in entities]
                    for key, entities in deps.items()
                },
            }
        except Exception as e:
            logger.error(f"Get dependents failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # =========================================================================
    # Statistics Methods
    # =========================================================================

    def get_code_stats(
        self,
        project_path: str,
    ) -> dict[str, Any]:
        """
        Get statistics about the indexed code.

        Args:
            project_path: Path to the project root

        Returns:
            Statistics including entity counts by type/language
        """
        try:
            manager = self._get_manager(project_path)
            stats = manager.get_code_stats()
            return {
                "success": True,
                "stats": stats,
            }
        except Exception as e:
            logger.error(f"Get code stats failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def reindex_project(
        self,
        project_path: str,
    ) -> dict[str, Any]:
        """
        Clear and rebuild the code index.

        Args:
            project_path: Path to the project root

        Returns:
            Index result with statistics
        """
        try:
            manager = self._get_manager(project_path)
            result = manager.reindex_project()
            return {
                "success": True,
                "result": result.to_dict(),
            }
        except Exception as e:
            logger.error(f"Reindex project failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_supported_languages(self) -> dict[str, Any]:
        """
        Get list of supported languages for code scanning.

        Returns:
            List of supported language names
        """
        try:
            from devflow.code.scanner import CodeScanner

            scanner = CodeScanner(".")
            languages = scanner.get_supported_languages()
            extensions = scanner.get_supported_extensions()

            return {
                "success": True,
                "languages": languages,
                "extensions": extensions,
            }
        except Exception as e:
            logger.error(f"Get supported languages failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_entity_types(self) -> dict[str, Any]:
        """
        Get available code entity types.

        Returns:
            List of entity types with display names
        """
        try:
            from devflow.code.models import CodeEntityType

            return {
                "success": True,
                "types": [
                    {
                        "id": t.value,
                        "name": t.display_name,
                        "icon": t.icon,
                    }
                    for t in CodeEntityType
                ],
            }
        except Exception as e:
            logger.error(f"Get entity types failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_relationship_types(self) -> dict[str, Any]:
        """
        Get available relationship types.

        Returns:
            List of relationship types with display names
        """
        try:
            from devflow.code.models import CodeRelationType

            return {
                "success": True,
                "types": [
                    {
                        "id": t.value,
                        "name": t.display_name,
                    }
                    for t in CodeRelationType
                ],
            }
        except Exception as e:
            logger.error(f"Get relationship types failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # =========================================================================
    # AI-Powered Methods
    # =========================================================================

    def explain_entity(
        self,
        entity_id: str,
        project_path: str,
        detail_level: str = "basic",
    ) -> dict[str, Any]:
        """
        Generate AI explanation for a code entity.

        Args:
            entity_id: ID of the entity
            project_path: Path to the project root
            detail_level: One of "brief", "basic", "detailed"

        Returns:
            Explanation with summary, algorithm steps, parameters, etc.
        """
        try:
            manager = self._get_manager(project_path)
            result = manager.explain_entity(entity_id, detail_level)
            if "error" in result:
                return {"success": False, "error": result["error"]}
            return {"success": True, **result}
        except Exception as e:
            logger.error(f"Explain entity failed: {e}")
            return {"success": False, "error": str(e)}

    def generate_docstring(
        self,
        entity_id: str,
        project_path: str,
    ) -> dict[str, Any]:
        """
        Auto-generate docstring for a code entity.

        Args:
            entity_id: ID of the entity
            project_path: Path to the project root

        Returns:
            Generated docstring
        """
        try:
            manager = self._get_manager(project_path)
            result = manager.generate_docstring(entity_id)
            if "error" in result:
                return {"success": False, "error": result["error"]}
            return {"success": True, **result}
        except Exception as e:
            logger.error(f"Generate docstring failed: {e}")
            return {"success": False, "error": str(e)}

    def suggest_improvements(
        self,
        entity_id: str,
        project_path: str,
    ) -> dict[str, Any]:
        """
        AI-suggested code improvements.

        Args:
            entity_id: ID of the entity
            project_path: Path to the project root

        Returns:
            List of improvement suggestions
        """
        try:
            manager = self._get_manager(project_path)
            result = manager.suggest_improvements(entity_id)
            if "error" in result:
                return {"success": False, "error": result["error"]}
            return {"success": True, **result}
        except Exception as e:
            logger.error(f"Suggest improvements failed: {e}")
            return {"success": False, "error": str(e)}

    def find_similar_code(
        self,
        entity_id: str,
        project_path: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        """
        Find semantically similar code using embeddings.

        Args:
            entity_id: ID of the entity
            project_path: Path to the project root
            limit: Maximum number of results

        Returns:
            List of similar entities with similarity scores
        """
        try:
            manager = self._get_manager(project_path)
            similar = manager.find_similar_code(entity_id, limit)
            return {
                "success": True,
                "entity_id": entity_id,
                "similar": similar,
                "count": len(similar),
            }
        except Exception as e:
            logger.error(f"Find similar code failed: {e}")
            return {"success": False, "error": str(e)}

    def detect_language(
        self,
        code: str,
    ) -> dict[str, Any]:
        """
        Detect programming language of code snippet.

        Args:
            code: Code snippet

        Returns:
            Detected language
        """
        try:
            manager = self._get_manager()
            result = manager.detect_language(code)
            if "error" in result:
                return {"success": False, "error": result["error"]}
            return {"success": True, **result}
        except Exception as e:
            logger.error(f"Detect language failed: {e}")
            return {"success": False, "error": str(e)}

    def get_ai_status(
        self,
        project_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Get AI availability status for code analysis.

        Args:
            project_path: Optional project path

        Returns:
            AI availability information
        """
        try:
            manager = self._get_manager(project_path)
            return manager.get_ai_status()
        except Exception as e:
            logger.error(f"Get AI status failed: {e}")
            return {"enabled": False, "available": False, "error": str(e)}
