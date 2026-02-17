"""
Semantic chunking for code entities.

Creates embedding-ready chunks from code entities with different
strategies for search, understanding, and relationship context.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from .models import (
    ClassEntity,
    CodeEntity,
    CodeEntityType,
    FunctionEntity,
    ImportEntity,
    ModuleEntity,
)
from .resolver import RelationshipResolver, Relationship

logger = logging.getLogger(__name__)


@dataclass
class CodeChunk:
    """A chunk of code ready for embedding."""

    entity_id: str
    chunk_type: str  # "signature", "implementation", "context", "docstring"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_id": self.entity_id,
            "chunk_type": self.chunk_type,
            "content": self.content,
            "metadata": self.metadata,
        }


class SemanticChunker:
    """Creates semantic chunks from code entities for embedding."""

    # Maximum chunk size (in characters)
    MAX_CHUNK_SIZE = 2000

    # Minimum content size to create a chunk
    MIN_CONTENT_SIZE = 20

    def __init__(
        self,
        entities: list[CodeEntity],
        resolver: RelationshipResolver | None = None,
    ):
        """
        Initialize the chunker.

        Args:
            entities: List of code entities to chunk
            resolver: Optional relationship resolver for context chunks
        """
        self.entities = entities
        self.resolver = resolver
        self._entity_map: dict[str, CodeEntity] = {e.id: e for e in entities}

    def create_chunks(
        self,
        include_signature: bool = True,
        include_implementation: bool = True,
        include_context: bool = True,
        include_docstring: bool = True,
    ) -> list[CodeChunk]:
        """
        Create all chunks for the entities.

        Args:
            include_signature: Include signature chunks
            include_implementation: Include implementation chunks
            include_context: Include relationship context chunks
            include_docstring: Include docstring-only chunks

        Returns:
            List of CodeChunk objects
        """
        chunks: list[CodeChunk] = []

        for entity in self.entities:
            entity_chunks = self.chunk_entity(
                entity,
                include_signature=include_signature,
                include_implementation=include_implementation,
                include_context=include_context,
                include_docstring=include_docstring,
            )
            chunks.extend(entity_chunks)

        logger.info(f"Created {len(chunks)} chunks from {len(self.entities)} entities")
        return chunks

    def chunk_entity(
        self,
        entity: CodeEntity,
        include_signature: bool = True,
        include_implementation: bool = True,
        include_context: bool = True,
        include_docstring: bool = True,
    ) -> list[CodeChunk]:
        """
        Create chunks for a single entity.

        Args:
            entity: The code entity to chunk
            include_*: Flags to control which chunk types to create

        Returns:
            List of CodeChunk objects for this entity
        """
        chunks: list[CodeChunk] = []
        base_metadata = self._get_base_metadata(entity)

        # Signature chunk (for search)
        if include_signature:
            sig_chunk = self._create_signature_chunk(entity, base_metadata)
            if sig_chunk:
                chunks.append(sig_chunk)

        # Implementation chunk (for understanding)
        if include_implementation:
            impl_chunk = self._create_implementation_chunk(entity, base_metadata)
            if impl_chunk:
                chunks.append(impl_chunk)

        # Context chunk (for relationships)
        if include_context and self.resolver:
            ctx_chunk = self._create_context_chunk(entity, base_metadata)
            if ctx_chunk:
                chunks.append(ctx_chunk)

        # Docstring chunk (for semantic search)
        if include_docstring and entity.docstring:
            doc_chunk = self._create_docstring_chunk(entity, base_metadata)
            if doc_chunk:
                chunks.append(doc_chunk)

        return chunks

    def _get_base_metadata(self, entity: CodeEntity) -> dict[str, Any]:
        """Get base metadata for an entity."""
        metadata = {
            "entity_id": entity.id,
            "entity_type": entity.entity_type.value,
            "language": entity.language,
            "file": entity.file_path,
            "line": entity.line_start,
            "line_end": entity.line_end,
            "qualified_name": entity.qualified_name,
            "name": entity.name,
            "tags": entity.tags,
        }

        # Add type-specific metadata
        if isinstance(entity, FunctionEntity):
            metadata.update({
                "is_async": entity.is_async,
                "is_method": entity.is_method,
                "is_generator": entity.is_generator,
                "parameter_count": len(entity.parameters),
                "complexity": entity.complexity,
                "return_type": entity.return_type,
                "parent_class": entity.parent_class,
            })

        elif isinstance(entity, ClassEntity):
            metadata.update({
                "is_abstract": entity.is_abstract,
                "is_dataclass": entity.is_dataclass,
                "is_protocol": entity.is_protocol,
                "base_classes": entity.base_classes,
                "method_count": len(entity.methods),
                "property_count": len(entity.properties),
            })

        return metadata

    def _create_signature_chunk(
        self, entity: CodeEntity, base_metadata: dict[str, Any]
    ) -> CodeChunk | None:
        """Create a signature chunk for search."""
        content_parts: list[str] = []

        if isinstance(entity, FunctionEntity):
            # Function signature
            content_parts.append(f"Function: {entity.name}")

            # Parameters
            if entity.parameters:
                params = ", ".join(str(p) for p in entity.parameters)
                content_parts.append(f"Parameters: {params}")

            # Return type
            if entity.return_type:
                content_parts.append(f"Returns: {entity.return_type}")

            # Decorators
            if entity.decorators:
                content_parts.append(f"Decorators: {', '.join(entity.decorators)}")

            # Docstring summary (first line)
            if entity.docstring:
                first_line = entity.docstring.split("\n")[0].strip()
                if first_line:
                    content_parts.append(f"Description: {first_line}")

            # Tags
            if entity.tags:
                content_parts.append(f"Tags: {', '.join(entity.tags)}")

        elif isinstance(entity, ClassEntity):
            # Class signature
            content_parts.append(f"Class: {entity.name}")

            # Base classes
            if entity.base_classes:
                content_parts.append(f"Extends: {', '.join(entity.base_classes)}")

            # Properties
            if entity.properties:
                props = [f"{p.name}: {p.type_annotation or 'Any'}" for p in entity.properties[:5]]
                content_parts.append(f"Properties: {', '.join(props)}")

            # Methods summary
            if entity.methods:
                method_names = [m.split(".")[-1] for m in entity.methods[:10]]
                content_parts.append(f"Methods: {', '.join(method_names)}")

            # Docstring summary
            if entity.docstring:
                first_line = entity.docstring.split("\n")[0].strip()
                if first_line:
                    content_parts.append(f"Description: {first_line}")

            # Tags
            if entity.tags:
                content_parts.append(f"Tags: {', '.join(entity.tags)}")

        elif isinstance(entity, ModuleEntity):
            # Module signature
            content_parts.append(f"Module: {entity.name}")

            # Summary
            if entity.docstring:
                first_line = entity.docstring.split("\n")[0].strip()
                if first_line:
                    content_parts.append(f"Description: {first_line}")

            # Contents summary
            if entity.classes:
                content_parts.append(f"Classes: {len(entity.classes)}")
            if entity.functions:
                content_parts.append(f"Functions: {len(entity.functions)}")

            # Exports
            if entity.exports:
                content_parts.append(f"Exports: {', '.join(entity.exports[:10])}")

        else:
            # Generic entity
            content_parts.append(f"{entity.entity_type.display_name}: {entity.name}")
            if entity.docstring:
                first_line = entity.docstring.split("\n")[0].strip()
                if first_line:
                    content_parts.append(f"Description: {first_line}")

        content = "\n".join(content_parts)

        if len(content) < self.MIN_CONTENT_SIZE:
            return None

        metadata = base_metadata.copy()
        metadata["chunk_type"] = "signature"

        return CodeChunk(
            entity_id=entity.id,
            chunk_type="signature",
            content=content[:self.MAX_CHUNK_SIZE],
            metadata=metadata,
        )

    def _create_implementation_chunk(
        self, entity: CodeEntity, base_metadata: dict[str, Any]
    ) -> CodeChunk | None:
        """Create an implementation chunk for understanding."""
        # Skip modules (too large)
        if entity.entity_type == CodeEntityType.MODULE:
            return None

        # Skip imports (not useful for implementation)
        if entity.entity_type == CodeEntityType.IMPORT:
            return None

        if not entity.source_code or len(entity.source_code) < self.MIN_CONTENT_SIZE:
            return None

        content_parts: list[str] = []

        # Header
        if isinstance(entity, FunctionEntity):
            content_parts.append(f"Function: {entity.name}")
        elif isinstance(entity, ClassEntity):
            content_parts.append(f"Class: {entity.name}")
        else:
            content_parts.append(f"{entity.entity_type.display_name}: {entity.name}")

        # Source code
        content_parts.append("Implementation:")
        content_parts.append(entity.source_code)

        content = "\n".join(content_parts)

        # Truncate if too long
        if len(content) > self.MAX_CHUNK_SIZE:
            content = content[:self.MAX_CHUNK_SIZE - 50] + "\n... (truncated)"

        metadata = base_metadata.copy()
        metadata["chunk_type"] = "implementation"
        metadata["source_lines"] = entity.line_end - entity.line_start + 1

        return CodeChunk(
            entity_id=entity.id,
            chunk_type="implementation",
            content=content,
            metadata=metadata,
        )

    def _create_context_chunk(
        self, entity: CodeEntity, base_metadata: dict[str, Any]
    ) -> CodeChunk | None:
        """Create a context chunk with relationship information."""
        if not self.resolver:
            return None

        content_parts: list[str] = []

        # Header
        if isinstance(entity, FunctionEntity):
            content_parts.append(f"Function: {entity.name}")
        elif isinstance(entity, ClassEntity):
            content_parts.append(f"Class: {entity.name}")
        else:
            content_parts.append(f"{entity.entity_type.display_name}: {entity.name}")

        # Get relationships
        deps = self.resolver.get_dependencies(entity.id)
        dependents = self.resolver.get_dependents(entity.id)

        # Calls (for functions)
        if isinstance(entity, FunctionEntity) and entity.calls:
            calls = entity.calls[:15]  # Limit
            content_parts.append(f"Calls: {', '.join(calls)}")

        # Called by
        if dependents.get("callers"):
            caller_names = [c.name for c in dependents["callers"][:10]]
            content_parts.append(f"Called by: {', '.join(caller_names)}")

        # Extends (for classes)
        if isinstance(entity, ClassEntity) and entity.base_classes:
            content_parts.append(f"Extends: {', '.join(entity.base_classes)}")

        # Subclasses
        if dependents.get("subclasses"):
            subclass_names = [s.name for s in dependents["subclasses"][:10]]
            content_parts.append(f"Subclasses: {', '.join(subclass_names)}")

        # Uses types (from type annotations)
        types_used = self._extract_types_used(entity)
        if types_used:
            content_parts.append(f"Uses types: {', '.join(types_used[:10])}")

        # Module context
        content_parts.append(f"From module: {entity.qualified_name.rsplit('.', 1)[0]}")

        # File location
        content_parts.append(f"File: {entity.file_path}:{entity.line_start}")

        content = "\n".join(content_parts)

        if len(content) < self.MIN_CONTENT_SIZE:
            return None

        metadata = base_metadata.copy()
        metadata["chunk_type"] = "context"
        metadata["caller_count"] = len(dependents.get("callers", []))
        metadata["callee_count"] = len(entity.calls) if isinstance(entity, FunctionEntity) else 0

        return CodeChunk(
            entity_id=entity.id,
            chunk_type="context",
            content=content[:self.MAX_CHUNK_SIZE],
            metadata=metadata,
        )

    def _create_docstring_chunk(
        self, entity: CodeEntity, base_metadata: dict[str, Any]
    ) -> CodeChunk | None:
        """Create a docstring-only chunk for semantic search."""
        if not entity.docstring:
            return None

        if len(entity.docstring) < self.MIN_CONTENT_SIZE:
            return None

        content_parts: list[str] = []

        # Header
        if isinstance(entity, FunctionEntity):
            content_parts.append(f"Documentation for function {entity.name}:")
        elif isinstance(entity, ClassEntity):
            content_parts.append(f"Documentation for class {entity.name}:")
        elif isinstance(entity, ModuleEntity):
            content_parts.append(f"Documentation for module {entity.name}:")
        else:
            content_parts.append(f"Documentation for {entity.name}:")

        content_parts.append(entity.docstring)

        content = "\n".join(content_parts)

        metadata = base_metadata.copy()
        metadata["chunk_type"] = "docstring"
        metadata["docstring_length"] = len(entity.docstring)

        return CodeChunk(
            entity_id=entity.id,
            chunk_type="docstring",
            content=content[:self.MAX_CHUNK_SIZE],
            metadata=metadata,
        )

    def _extract_types_used(self, entity: CodeEntity) -> list[str]:
        """Extract type names used in an entity."""
        types: set[str] = set()

        if isinstance(entity, FunctionEntity):
            # Parameter types
            for param in entity.parameters:
                if param.type_annotation:
                    types.update(self._parse_type_names(param.type_annotation))

            # Return type
            if entity.return_type:
                types.update(self._parse_type_names(entity.return_type))

        elif isinstance(entity, ClassEntity):
            # Base classes
            for base in entity.base_classes:
                types.update(self._parse_type_names(base))

            # Property types
            for prop in entity.properties:
                if prop.type_annotation:
                    types.update(self._parse_type_names(prop.type_annotation))

        # Filter out common built-in types
        builtins = {
            "str", "int", "float", "bool", "None", "Any", "List", "Dict",
            "Set", "Tuple", "Optional", "Union", "Callable", "Type",
            "Awaitable", "Coroutine", "Generator", "Iterator",
            "string", "number", "boolean", "void", "any", "unknown",
            "Array", "Object", "Promise", "Map", "Set",
        }
        types = {t for t in types if t not in builtins}

        return sorted(types)

    def _parse_type_names(self, type_str: str) -> list[str]:
        """Parse type names from a type annotation string."""
        import re

        # Remove generic brackets content for simple extraction
        # e.g., "Dict[str, List[int]]" -> ["Dict", "List"]
        names: list[str] = []

        # Split on common delimiters
        parts = re.split(r"[\[\],\s|]+", type_str)

        for part in parts:
            # Clean up
            part = part.strip().strip("()")
            if part and part[0].isupper() and part.isidentifier():
                names.append(part)

        return names

    def get_chunk_stats(self, chunks: list[CodeChunk]) -> dict[str, Any]:
        """Get statistics about generated chunks."""
        stats = {
            "total_chunks": len(chunks),
            "by_type": {},
            "by_entity_type": {},
            "avg_content_length": 0,
            "max_content_length": 0,
        }

        if not chunks:
            return stats

        type_counts: dict[str, int] = {}
        entity_type_counts: dict[str, int] = {}
        total_length = 0
        max_length = 0

        for chunk in chunks:
            # Count by chunk type
            type_counts[chunk.chunk_type] = type_counts.get(chunk.chunk_type, 0) + 1

            # Count by entity type
            entity_type = chunk.metadata.get("entity_type", "unknown")
            entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + 1

            # Track lengths
            length = len(chunk.content)
            total_length += length
            max_length = max(max_length, length)

        stats["by_type"] = type_counts
        stats["by_entity_type"] = entity_type_counts
        stats["avg_content_length"] = total_length // len(chunks)
        stats["max_content_length"] = max_length

        return stats
