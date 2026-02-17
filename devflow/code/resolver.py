"""
Relationship resolver for code entities.

Analyzes code entities to discover relationships like:
- Function calls (CALLS/CALLED_BY)
- Import dependencies (IMPORTS)
- Class inheritance (EXTENDS)
- Type usage (USES, TYPED_AS)
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .models import (
    ClassEntity,
    CodeEntity,
    CodeEntityType,
    CodeRelationType,
    FunctionEntity,
    ImportEntity,
    ModuleEntity,
)

logger = logging.getLogger(__name__)


@dataclass
class Relationship:
    """A relationship between two code entities."""

    source_id: str
    target_id: str
    relationship_type: CodeRelationType
    source_name: str = ""
    target_name: str = ""
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type.value,
            "source_name": self.source_name,
            "target_name": self.target_name,
            "weight": self.weight,
            "metadata": self.metadata,
        }


@dataclass
class ResolutionResult:
    """Result of relationship resolution."""

    relationships: list[Relationship]
    unresolved_calls: list[tuple[str, str]]  # (entity_id, call_name)
    unresolved_imports: list[tuple[str, str]]  # (entity_id, import_name)
    stats: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "relationship_count": len(self.relationships),
            "relationships_by_type": {
                rt.value: len([r for r in self.relationships if r.relationship_type == rt])
                for rt in CodeRelationType
            },
            "unresolved_calls": len(self.unresolved_calls),
            "unresolved_imports": len(self.unresolved_imports),
            "stats": self.stats,
        }


class RelationshipResolver:
    """Resolves relationships between code entities."""

    def __init__(self, entities: list[CodeEntity]):
        """
        Initialize the resolver with a set of entities.

        Args:
            entities: List of code entities to analyze
        """
        self.entities = entities

        # Build lookup indexes
        self._by_id: dict[str, CodeEntity] = {}
        self._by_qualified_name: dict[str, CodeEntity] = {}
        self._by_name: dict[str, list[CodeEntity]] = defaultdict(list)
        self._by_type: dict[CodeEntityType, list[CodeEntity]] = defaultdict(list)
        self._by_file: dict[str, list[CodeEntity]] = defaultdict(list)

        self._build_indexes()

    def _build_indexes(self) -> None:
        """Build lookup indexes for entities."""
        for entity in self.entities:
            self._by_id[entity.id] = entity
            self._by_qualified_name[entity.qualified_name] = entity
            self._by_name[entity.name].append(entity)
            self._by_type[entity.entity_type].append(entity)
            self._by_file[entity.file_path].append(entity)

    def resolve(self) -> ResolutionResult:
        """
        Resolve all relationships between entities.

        Returns:
            ResolutionResult with discovered relationships
        """
        relationships: list[Relationship] = []
        unresolved_calls: list[tuple[str, str]] = []
        unresolved_imports: list[tuple[str, str]] = []

        stats = {
            "functions_analyzed": 0,
            "classes_analyzed": 0,
            "imports_analyzed": 0,
            "calls_resolved": 0,
            "inheritance_resolved": 0,
        }

        # Resolve function calls
        for entity in self._by_type[CodeEntityType.FUNCTION]:
            if isinstance(entity, FunctionEntity):
                stats["functions_analyzed"] += 1
                call_rels, unresolved = self._resolve_calls(entity)
                relationships.extend(call_rels)
                unresolved_calls.extend(unresolved)
                stats["calls_resolved"] += len(call_rels)

        for entity in self._by_type[CodeEntityType.METHOD]:
            if isinstance(entity, FunctionEntity):
                stats["functions_analyzed"] += 1
                call_rels, unresolved = self._resolve_calls(entity)
                relationships.extend(call_rels)
                unresolved_calls.extend(unresolved)
                stats["calls_resolved"] += len(call_rels)

        # Resolve class inheritance
        for entity in self._by_type[CodeEntityType.CLASS]:
            if isinstance(entity, ClassEntity):
                stats["classes_analyzed"] += 1
                inherit_rels = self._resolve_inheritance(entity)
                relationships.extend(inherit_rels)
                stats["inheritance_resolved"] += len(inherit_rels)

                # Resolve class containment
                contains_rels = self._resolve_class_containment(entity)
                relationships.extend(contains_rels)

        # Resolve imports
        for entity in self._by_type[CodeEntityType.IMPORT]:
            if isinstance(entity, ImportEntity):
                stats["imports_analyzed"] += 1
                import_rels, unresolved = self._resolve_imports(entity)
                relationships.extend(import_rels)
                unresolved_imports.extend(unresolved)

        # Resolve module containment
        for entity in self._by_type[CodeEntityType.MODULE]:
            if isinstance(entity, ModuleEntity):
                contains_rels = self._resolve_module_containment(entity)
                relationships.extend(contains_rels)

        # Add reverse relationships (CALLED_BY)
        reverse_rels = self._create_reverse_relationships(relationships)
        relationships.extend(reverse_rels)

        logger.info(
            f"Resolved {len(relationships)} relationships: "
            f"{stats['calls_resolved']} calls, {stats['inheritance_resolved']} inheritance"
        )

        return ResolutionResult(
            relationships=relationships,
            unresolved_calls=unresolved_calls,
            unresolved_imports=unresolved_imports,
            stats=stats,
        )

    def _resolve_calls(
        self, entity: FunctionEntity
    ) -> tuple[list[Relationship], list[tuple[str, str]]]:
        """Resolve function call relationships."""
        relationships: list[Relationship] = []
        unresolved: list[tuple[str, str]] = []

        for call_name in entity.calls:
            target = self._find_call_target(call_name, entity)

            if target:
                relationships.append(
                    Relationship(
                        source_id=entity.id,
                        target_id=target.id,
                        relationship_type=CodeRelationType.CALLS,
                        source_name=entity.qualified_name,
                        target_name=target.qualified_name,
                        metadata={"call_name": call_name},
                    )
                )
            else:
                unresolved.append((entity.id, call_name))

        return relationships, unresolved

    def _find_call_target(
        self, call_name: str, caller: FunctionEntity
    ) -> CodeEntity | None:
        """
        Find the target of a function call.

        Args:
            call_name: The name/path of the called function
            caller: The calling function entity

        Returns:
            The target entity or None if not found
        """
        # Handle method calls (e.g., "self.method" or "obj.method")
        if "." in call_name:
            parts = call_name.split(".")

            # Self/this method call
            if parts[0] in ("self", "this") and caller.parent_class:
                method_name = parts[-1]
                # Look for method in same class
                qualified = f"{caller.parent_class}.{method_name}"
                if qualified in self._by_qualified_name:
                    return self._by_qualified_name[qualified]

            # Object method call - try to resolve the full path
            for i in range(len(parts), 0, -1):
                partial = ".".join(parts[:i])
                matches = [
                    e for e in self._by_name.get(parts[-1], [])
                    if partial in e.qualified_name
                ]
                if matches:
                    # Prefer same-file matches
                    same_file = [m for m in matches if m.file_path == caller.file_path]
                    return same_file[0] if same_file else matches[0]

        # Direct function call
        # 1. Check exact qualified name match
        if call_name in self._by_qualified_name:
            return self._by_qualified_name[call_name]

        # 2. Check by simple name
        candidates = self._by_name.get(call_name, [])

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # 3. Multiple candidates - prefer same file
        same_file = [c for c in candidates if c.file_path == caller.file_path]
        if same_file:
            return same_file[0]

        # 4. Prefer same language
        same_lang = [c for c in candidates if c.language == caller.language]
        if same_lang:
            return same_lang[0]

        # Return first match
        return candidates[0]

    def _resolve_inheritance(
        self, entity: ClassEntity
    ) -> list[Relationship]:
        """Resolve class inheritance relationships."""
        relationships: list[Relationship] = []

        for base_class in entity.base_classes:
            # Try to find the base class
            target = self._find_class(base_class, entity)

            if target:
                relationships.append(
                    Relationship(
                        source_id=entity.id,
                        target_id=target.id,
                        relationship_type=CodeRelationType.EXTENDS,
                        source_name=entity.qualified_name,
                        target_name=target.qualified_name,
                        metadata={"base_class": base_class},
                    )
                )

        return relationships

    def _find_class(
        self, class_name: str, context: CodeEntity
    ) -> ClassEntity | None:
        """
        Find a class by name.

        Args:
            class_name: Name of the class to find
            context: Context entity for resolution

        Returns:
            The class entity or None if not found
        """
        # Remove generic type parameters
        class_name = re.sub(r"\[.*\]", "", class_name).strip()

        # Check qualified name
        if class_name in self._by_qualified_name:
            entity = self._by_qualified_name[class_name]
            if entity.entity_type == CodeEntityType.CLASS:
                return entity  # type: ignore

        # Check by simple name
        candidates = [
            e for e in self._by_name.get(class_name, [])
            if e.entity_type == CodeEntityType.CLASS
        ]

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]  # type: ignore

        # Prefer same file
        same_file = [c for c in candidates if c.file_path == context.file_path]
        if same_file:
            return same_file[0]  # type: ignore

        return candidates[0]  # type: ignore

    def _resolve_class_containment(
        self, entity: ClassEntity
    ) -> list[Relationship]:
        """Resolve class method containment relationships."""
        relationships: list[Relationship] = []

        for method_name in entity.methods:
            # Find the method entity
            if method_name in self._by_qualified_name:
                method = self._by_qualified_name[method_name]
                relationships.append(
                    Relationship(
                        source_id=entity.id,
                        target_id=method.id,
                        relationship_type=CodeRelationType.CONTAINS,
                        source_name=entity.qualified_name,
                        target_name=method.qualified_name,
                    )
                )

        return relationships

    def _resolve_module_containment(
        self, entity: ModuleEntity
    ) -> list[Relationship]:
        """Resolve module containment relationships."""
        relationships: list[Relationship] = []

        # Find all entities in this file
        file_entities = self._by_file.get(entity.file_path, [])

        for file_entity in file_entities:
            # Skip the module itself and imports
            if file_entity.id == entity.id:
                continue
            if file_entity.entity_type == CodeEntityType.IMPORT:
                continue
            # Skip methods (they're contained by classes)
            if file_entity.entity_type == CodeEntityType.METHOD:
                continue

            relationships.append(
                Relationship(
                    source_id=entity.id,
                    target_id=file_entity.id,
                    relationship_type=CodeRelationType.CONTAINS,
                    source_name=entity.qualified_name,
                    target_name=file_entity.qualified_name,
                )
            )

        return relationships

    def _resolve_imports(
        self, entity: ImportEntity
    ) -> tuple[list[Relationship], list[tuple[str, str]]]:
        """Resolve import relationships."""
        relationships: list[Relationship] = []
        unresolved: list[tuple[str, str]] = []

        # Get the module entity for this file
        module = self._get_file_module(entity.file_path)

        if not module:
            return relationships, unresolved

        # For each imported name, try to find the target
        for name in entity.names:
            if entity.module:
                # from module import name
                full_name = f"{entity.module}.{name}"
            else:
                # import name
                full_name = name

            # Try to find the imported entity
            target = (
                self._by_qualified_name.get(full_name)
                or self._by_qualified_name.get(name)
            )

            # Also check if it's a module
            if not target:
                # Check if any entity's module matches
                for mod in self._by_type[CodeEntityType.MODULE]:
                    if mod.qualified_name == entity.module or mod.name == entity.module:
                        target = mod
                        break

            if target:
                relationships.append(
                    Relationship(
                        source_id=module.id,
                        target_id=target.id,
                        relationship_type=CodeRelationType.IMPORTS,
                        source_name=module.qualified_name,
                        target_name=target.qualified_name,
                        metadata={
                            "import_name": name,
                            "from_module": entity.module,
                            "alias": entity.aliases.get(name),
                        },
                    )
                )
            else:
                unresolved.append((entity.id, full_name))

        return relationships, unresolved

    def _get_file_module(self, file_path: str) -> ModuleEntity | None:
        """Get the module entity for a file."""
        for entity in self._by_file.get(file_path, []):
            if entity.entity_type == CodeEntityType.MODULE:
                return entity  # type: ignore
        return None

    def _create_reverse_relationships(
        self, relationships: list[Relationship]
    ) -> list[Relationship]:
        """Create reverse relationships (e.g., CALLED_BY from CALLS)."""
        reverse: list[Relationship] = []

        for rel in relationships:
            inverse_type = rel.relationship_type.inverse
            if inverse_type:
                reverse.append(
                    Relationship(
                        source_id=rel.target_id,
                        target_id=rel.source_id,
                        relationship_type=inverse_type,
                        source_name=rel.target_name,
                        target_name=rel.source_name,
                        weight=rel.weight,
                        metadata=rel.metadata,
                    )
                )

        return reverse

    def get_callers(self, entity_id: str) -> list[CodeEntity]:
        """Get all entities that call the given entity."""
        callers: list[CodeEntity] = []

        for entity in self.entities:
            if isinstance(entity, FunctionEntity):
                for call in entity.calls:
                    target = self._find_call_target(call, entity)
                    if target and target.id == entity_id:
                        callers.append(entity)
                        break

        return callers

    def get_callees(self, entity_id: str) -> list[CodeEntity]:
        """Get all entities called by the given entity."""
        entity = self._by_id.get(entity_id)
        if not entity or not isinstance(entity, FunctionEntity):
            return []

        callees: list[CodeEntity] = []
        for call in entity.calls:
            target = self._find_call_target(call, entity)
            if target:
                callees.append(target)

        return callees

    def get_dependencies(self, entity_id: str) -> dict[str, list[CodeEntity]]:
        """
        Get all dependencies of an entity.

        Returns dict with keys: 'imports', 'calls', 'extends', 'uses'
        """
        entity = self._by_id.get(entity_id)
        if not entity:
            return {"imports": [], "calls": [], "extends": [], "uses": []}

        deps: dict[str, list[CodeEntity]] = {
            "imports": [],
            "calls": [],
            "extends": [],
            "uses": [],
        }

        # Get imports from same file
        for imp in self._by_file.get(entity.file_path, []):
            if imp.entity_type == CodeEntityType.IMPORT:
                deps["imports"].append(imp)

        # Get function calls
        if isinstance(entity, FunctionEntity):
            deps["calls"] = self.get_callees(entity_id)

        # Get base classes
        if isinstance(entity, ClassEntity):
            for base_class in entity.base_classes:
                base = self._find_class(base_class, entity)
                if base:
                    deps["extends"].append(base)

        return deps

    def get_dependents(self, entity_id: str) -> dict[str, list[CodeEntity]]:
        """
        Get all entities that depend on the given entity.

        Returns dict with keys: 'callers', 'subclasses', 'importers'
        """
        entity = self._by_id.get(entity_id)
        if not entity:
            return {"callers": [], "subclasses": [], "importers": []}

        deps: dict[str, list[CodeEntity]] = {
            "callers": [],
            "subclasses": [],
            "importers": [],
        }

        # Get callers
        deps["callers"] = self.get_callers(entity_id)

        # Get subclasses
        if entity.entity_type == CodeEntityType.CLASS:
            for cls in self._by_type[CodeEntityType.CLASS]:
                if isinstance(cls, ClassEntity):
                    if entity.name in cls.base_classes:
                        deps["subclasses"].append(cls)

        return deps
