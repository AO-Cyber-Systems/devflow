"""Tests for the semantic chunker."""

import pytest

from devflow.code.models import (
    CodeEntityType,
    FunctionEntity,
    ClassEntity,
    ModuleEntity,
    Parameter,
    Property,
)
from devflow.code.resolver import RelationshipResolver
from devflow.code.chunker import SemanticChunker, CodeChunk


class TestCodeChunk:
    """Tests for CodeChunk dataclass."""

    def test_basic_chunk(self):
        """Test basic chunk creation."""
        chunk = CodeChunk(
            entity_id="test123",
            chunk_type="signature",
            content="Function: test_func",
        )
        assert chunk.entity_id == "test123"
        assert chunk.chunk_type == "signature"

    def test_chunk_to_dict(self):
        """Test chunk serialization."""
        chunk = CodeChunk(
            entity_id="test123",
            chunk_type="implementation",
            content="def test(): pass",
            metadata={"language": "python"},
        )
        data = chunk.to_dict()

        assert data["entity_id"] == "test123"
        assert data["chunk_type"] == "implementation"
        assert data["metadata"]["language"] == "python"


class TestSemanticChunker:
    """Tests for SemanticChunker."""

    @pytest.fixture
    def sample_entities(self):
        """Create sample entities for testing."""
        entities = []

        # Module
        mod = ModuleEntity(
            id="mod1",
            name="utils",
            qualified_name="utils",
            entity_type=CodeEntityType.MODULE,
            file_path="/path/utils.py",
            line_start=1,
            line_end=100,
            language="python",
            source_code="",
            docstring="Utility functions for data processing.",
        )
        entities.append(mod)

        # Function with docstring
        func1 = FunctionEntity(
            id="func1",
            name="process_data",
            qualified_name="utils.process_data",
            entity_type=CodeEntityType.FUNCTION,
            file_path="/path/utils.py",
            line_start=10,
            line_end=25,
            language="python",
            source_code="def process_data(input: dict) -> list:\n    return [input]",
            docstring="Process input data and return a list.\n\nArgs:\n    input: Input dictionary",
            parameters=[
                Parameter(name="input", type_annotation="dict"),
            ],
            return_type="list",
            is_async=False,
            calls=["helper", "transform"],
        )
        entities.append(func1)

        # Async function
        func2 = FunctionEntity(
            id="func2",
            name="fetch_async",
            qualified_name="utils.fetch_async",
            entity_type=CodeEntityType.FUNCTION,
            file_path="/path/utils.py",
            line_start=30,
            line_end=40,
            language="python",
            source_code="async def fetch_async(url: str) -> dict:\n    pass",
            docstring="Fetch data asynchronously.",
            parameters=[
                Parameter(name="url", type_annotation="str"),
            ],
            return_type="dict",
            is_async=True,
            tags=["async"],
        )
        entities.append(func2)

        # Class
        cls1 = ClassEntity(
            id="cls1",
            name="DataProcessor",
            qualified_name="utils.DataProcessor",
            entity_type=CodeEntityType.CLASS,
            file_path="/path/utils.py",
            line_start=50,
            line_end=80,
            language="python",
            source_code="class DataProcessor:\n    pass",
            docstring="A class for processing data.",
            base_classes=["BaseProcessor"],
            methods=["utils.DataProcessor.run", "utils.DataProcessor.stop"],
            properties=[
                Property(name="config", type_annotation="dict"),
            ],
        )
        entities.append(cls1)

        return entities

    def test_chunker_initialization(self, sample_entities):
        """Test chunker initialization."""
        chunker = SemanticChunker(sample_entities)
        assert len(chunker.entities) == len(sample_entities)

    def test_create_all_chunks(self, sample_entities):
        """Test creating all chunk types."""
        chunker = SemanticChunker(sample_entities)
        chunks = chunker.create_chunks()

        assert len(chunks) > 0

        # Should have multiple chunk types
        chunk_types = {c.chunk_type for c in chunks}
        assert "signature" in chunk_types
        assert "docstring" in chunk_types

    def test_signature_chunks(self, sample_entities):
        """Test signature chunk creation."""
        chunker = SemanticChunker(sample_entities)
        chunks = chunker.create_chunks(
            include_signature=True,
            include_implementation=False,
            include_context=False,
            include_docstring=False,
        )

        sig_chunks = [c for c in chunks if c.chunk_type == "signature"]
        assert len(sig_chunks) > 0

        # Check function signature chunk
        func_sig = next((c for c in sig_chunks if c.metadata.get("name") == "process_data"), None)
        assert func_sig is not None
        assert "Function: process_data" in func_sig.content
        assert "input: dict" in func_sig.content
        assert "Returns: list" in func_sig.content

    def test_implementation_chunks(self, sample_entities):
        """Test implementation chunk creation."""
        chunker = SemanticChunker(sample_entities)
        chunks = chunker.create_chunks(
            include_signature=False,
            include_implementation=True,
            include_context=False,
            include_docstring=False,
        )

        impl_chunks = [c for c in chunks if c.chunk_type == "implementation"]
        assert len(impl_chunks) > 0

        # Check function implementation chunk
        func_impl = next((c for c in impl_chunks if c.metadata.get("name") == "process_data"), None)
        assert func_impl is not None
        assert "def process_data" in func_impl.content

    def test_docstring_chunks(self, sample_entities):
        """Test docstring chunk creation."""
        chunker = SemanticChunker(sample_entities)
        chunks = chunker.create_chunks(
            include_signature=False,
            include_implementation=False,
            include_context=False,
            include_docstring=True,
        )

        doc_chunks = [c for c in chunks if c.chunk_type == "docstring"]
        assert len(doc_chunks) > 0

        # Each entity with docstring should have a chunk
        for entity in sample_entities:
            if entity.docstring and len(entity.docstring) >= 20:
                doc_chunk = next(
                    (c for c in doc_chunks if c.entity_id == entity.id),
                    None,
                )
                assert doc_chunk is not None
                assert entity.docstring in doc_chunk.content

    def test_context_chunks_with_resolver(self, sample_entities):
        """Test context chunk creation with resolver."""
        resolver = RelationshipResolver(sample_entities)
        chunker = SemanticChunker(sample_entities, resolver)

        chunks = chunker.create_chunks(
            include_signature=False,
            include_implementation=False,
            include_context=True,
            include_docstring=False,
        )

        ctx_chunks = [c for c in chunks if c.chunk_type == "context"]
        assert len(ctx_chunks) > 0

        # Check function context chunk
        func_ctx = next((c for c in ctx_chunks if c.metadata.get("name") == "process_data"), None)
        assert func_ctx is not None
        assert "Calls:" in func_ctx.content

    def test_chunk_metadata(self, sample_entities):
        """Test that chunks have proper metadata."""
        chunker = SemanticChunker(sample_entities)
        chunks = chunker.create_chunks()

        for chunk in chunks:
            # All chunks should have basic metadata
            assert "entity_id" in chunk.metadata
            assert "entity_type" in chunk.metadata
            assert "language" in chunk.metadata
            assert "file" in chunk.metadata

    def test_function_chunk_metadata(self, sample_entities):
        """Test function-specific metadata."""
        chunker = SemanticChunker(sample_entities)
        chunks = chunker.create_chunks()

        func_chunks = [c for c in chunks if c.metadata.get("entity_type") == "function"]
        assert len(func_chunks) > 0

        for chunk in func_chunks:
            assert "is_async" in chunk.metadata
            assert "parameter_count" in chunk.metadata

    def test_class_chunk_metadata(self, sample_entities):
        """Test class-specific metadata."""
        chunker = SemanticChunker(sample_entities)
        chunks = chunker.create_chunks()

        class_chunks = [c for c in chunks if c.metadata.get("entity_type") == "class"]
        assert len(class_chunks) > 0

        for chunk in class_chunks:
            assert "is_abstract" in chunk.metadata
            assert "is_dataclass" in chunk.metadata

    def test_chunk_stats(self, sample_entities):
        """Test chunk statistics."""
        chunker = SemanticChunker(sample_entities)
        chunks = chunker.create_chunks()
        stats = chunker.get_chunk_stats(chunks)

        assert stats["total_chunks"] == len(chunks)
        assert "by_type" in stats
        assert "by_entity_type" in stats
        assert stats["avg_content_length"] > 0

    def test_chunk_size_limit(self, sample_entities):
        """Test that chunks respect size limits."""
        # Create a function with very long source
        long_source = "def long_func():\n" + "    x = 1\n" * 500
        func = FunctionEntity(
            id="long_func",
            name="long_func",
            qualified_name="utils.long_func",
            entity_type=CodeEntityType.FUNCTION,
            file_path="/path/utils.py",
            line_start=1,
            line_end=500,
            language="python",
            source_code=long_source,
        )

        chunker = SemanticChunker([func])
        chunks = chunker.create_chunks()

        for chunk in chunks:
            assert len(chunk.content) <= SemanticChunker.MAX_CHUNK_SIZE

    def test_empty_entities(self):
        """Test chunker with no entities."""
        chunker = SemanticChunker([])
        chunks = chunker.create_chunks()

        assert chunks == []

    def test_selective_chunk_creation(self, sample_entities):
        """Test creating only specific chunk types."""
        chunker = SemanticChunker(sample_entities)

        # Only signatures
        sig_only = chunker.create_chunks(
            include_signature=True,
            include_implementation=False,
            include_context=False,
            include_docstring=False,
        )
        assert all(c.chunk_type == "signature" for c in sig_only)

        # Only implementation
        impl_only = chunker.create_chunks(
            include_signature=False,
            include_implementation=True,
            include_context=False,
            include_docstring=False,
        )
        assert all(c.chunk_type == "implementation" for c in impl_only)

    def test_chunk_entity_single(self, sample_entities):
        """Test chunking a single entity."""
        func = sample_entities[1]  # process_data function
        chunker = SemanticChunker(sample_entities)

        chunks = chunker.chunk_entity(func)

        # Should have multiple chunk types for this entity
        assert len(chunks) > 0
        assert all(c.entity_id == func.id for c in chunks)
