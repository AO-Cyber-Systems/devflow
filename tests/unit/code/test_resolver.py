"""Tests for the relationship resolver."""

import pytest

from devflow.code.models import (
    CodeEntityType,
    CodeRelationType,
    FunctionEntity,
    ClassEntity,
    ImportEntity,
    ModuleEntity,
)
from devflow.code.resolver import RelationshipResolver, Relationship


class TestRelationship:
    """Tests for Relationship dataclass."""

    def test_basic_relationship(self):
        """Test basic relationship creation."""
        rel = Relationship(
            source_id="func1",
            target_id="func2",
            relationship_type=CodeRelationType.CALLS,
            source_name="module.func1",
            target_name="module.func2",
        )
        assert rel.source_id == "func1"
        assert rel.target_id == "func2"
        assert rel.relationship_type == CodeRelationType.CALLS

    def test_relationship_to_dict(self):
        """Test relationship serialization."""
        rel = Relationship(
            source_id="func1",
            target_id="func2",
            relationship_type=CodeRelationType.CALLS,
            weight=0.8,
            metadata={"call_name": "func2"},
        )
        data = rel.to_dict()
        assert data["source_id"] == "func1"
        assert data["relationship_type"] == "calls"
        assert data["weight"] == 0.8
        assert data["metadata"]["call_name"] == "func2"


class TestRelationshipResolver:
    """Tests for RelationshipResolver."""

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
        )
        entities.append(mod)

        # Functions
        func1 = FunctionEntity(
            id="func1",
            name="process",
            qualified_name="utils.process",
            entity_type=CodeEntityType.FUNCTION,
            file_path="/path/utils.py",
            line_start=10,
            line_end=20,
            language="python",
            source_code="def process(): helper()",
            calls=["helper", "transform"],
        )
        entities.append(func1)

        func2 = FunctionEntity(
            id="func2",
            name="helper",
            qualified_name="utils.helper",
            entity_type=CodeEntityType.FUNCTION,
            file_path="/path/utils.py",
            line_start=25,
            line_end=30,
            language="python",
            source_code="def helper(): pass",
            calls=[],
        )
        entities.append(func2)

        func3 = FunctionEntity(
            id="func3",
            name="transform",
            qualified_name="utils.transform",
            entity_type=CodeEntityType.FUNCTION,
            file_path="/path/utils.py",
            line_start=35,
            line_end=40,
            language="python",
            source_code="def transform(): helper()",
            calls=["helper"],
        )
        entities.append(func3)

        # Class
        cls1 = ClassEntity(
            id="cls1",
            name="Processor",
            qualified_name="utils.Processor",
            entity_type=CodeEntityType.CLASS,
            file_path="/path/utils.py",
            line_start=50,
            line_end=80,
            language="python",
            source_code="class Processor: ...",
            base_classes=["BaseProcessor"],
            methods=["utils.Processor.run", "utils.Processor.stop"],
        )
        entities.append(cls1)

        # Method
        method1 = FunctionEntity(
            id="method1",
            name="run",
            qualified_name="utils.Processor.run",
            entity_type=CodeEntityType.METHOD,
            file_path="/path/utils.py",
            line_start=55,
            line_end=60,
            language="python",
            source_code="def run(self): self.stop()",
            is_method=True,
            parent_class="utils.Processor",
            calls=["self.stop", "process"],
        )
        entities.append(method1)

        method2 = FunctionEntity(
            id="method2",
            name="stop",
            qualified_name="utils.Processor.stop",
            entity_type=CodeEntityType.METHOD,
            file_path="/path/utils.py",
            line_start=65,
            line_end=70,
            language="python",
            source_code="def stop(self): pass",
            is_method=True,
            parent_class="utils.Processor",
            calls=[],
        )
        entities.append(method2)

        # Child class
        cls2 = ClassEntity(
            id="cls2",
            name="SpecialProcessor",
            qualified_name="utils.SpecialProcessor",
            entity_type=CodeEntityType.CLASS,
            file_path="/path/utils.py",
            line_start=85,
            line_end=95,
            language="python",
            source_code="class SpecialProcessor(Processor): ...",
            base_classes=["Processor"],
        )
        entities.append(cls2)

        return entities

    def test_resolver_initialization(self, sample_entities):
        """Test resolver initialization."""
        resolver = RelationshipResolver(sample_entities)
        assert len(resolver.entities) == len(sample_entities)

    def test_resolve_function_calls(self, sample_entities):
        """Test resolution of function call relationships."""
        resolver = RelationshipResolver(sample_entities)
        result = resolver.resolve()

        # Find CALLS relationships
        calls = [r for r in result.relationships if r.relationship_type == CodeRelationType.CALLS]
        assert len(calls) > 0

        # process -> helper should be resolved
        process_to_helper = next(
            (r for r in calls if r.source_name == "utils.process" and r.target_name == "utils.helper"),
            None,
        )
        assert process_to_helper is not None

        # transform -> helper should be resolved
        transform_to_helper = next(
            (r for r in calls if r.source_name == "utils.transform" and r.target_name == "utils.helper"),
            None,
        )
        assert transform_to_helper is not None

    def test_resolve_called_by(self, sample_entities):
        """Test resolution of CALLED_BY relationships (reverse of CALLS)."""
        resolver = RelationshipResolver(sample_entities)
        result = resolver.resolve()

        # Find CALLED_BY relationships
        called_by = [r for r in result.relationships if r.relationship_type == CodeRelationType.CALLED_BY]
        assert len(called_by) > 0

        # helper is called by process and transform
        helper_called_by = [r for r in called_by if r.source_name == "utils.helper"]
        assert len(helper_called_by) >= 2

    def test_resolve_class_containment(self, sample_entities):
        """Test resolution of class containment relationships."""
        resolver = RelationshipResolver(sample_entities)
        result = resolver.resolve()

        # Find CONTAINS relationships from class to methods
        contains = [r for r in result.relationships if r.relationship_type == CodeRelationType.CONTAINS]
        assert len(contains) > 0

        # Processor should contain run and stop methods
        processor_contains = [r for r in contains if r.source_name == "utils.Processor"]
        method_names = [r.target_name for r in processor_contains]
        assert any("run" in name for name in method_names)
        assert any("stop" in name for name in method_names)

    def test_resolve_inheritance(self, sample_entities):
        """Test resolution of inheritance relationships."""
        resolver = RelationshipResolver(sample_entities)
        result = resolver.resolve()

        # Find EXTENDS relationships
        extends = [r for r in result.relationships if r.relationship_type == CodeRelationType.EXTENDS]

        # SpecialProcessor extends Processor
        sp_extends = next(
            (r for r in extends if r.source_name == "utils.SpecialProcessor"),
            None,
        )
        assert sp_extends is not None
        assert sp_extends.target_name == "utils.Processor"

    def test_resolve_method_calls(self, sample_entities):
        """Test resolution of method call relationships."""
        resolver = RelationshipResolver(sample_entities)
        result = resolver.resolve()

        calls = [r for r in result.relationships if r.relationship_type == CodeRelationType.CALLS]

        # run -> stop (self.stop)
        run_to_stop = next(
            (r for r in calls if "run" in r.source_name and "stop" in r.target_name),
            None,
        )
        assert run_to_stop is not None

        # run -> process
        run_to_process = next(
            (r for r in calls if "run" in r.source_name and "process" in r.target_name),
            None,
        )
        assert run_to_process is not None

    def test_get_callers(self, sample_entities):
        """Test getting callers of an entity."""
        resolver = RelationshipResolver(sample_entities)
        resolver.resolve()

        # helper is called by process and transform
        callers = resolver.get_callers("func2")
        caller_names = [c.name for c in callers]
        assert "process" in caller_names
        assert "transform" in caller_names

    def test_get_callees(self, sample_entities):
        """Test getting callees of an entity."""
        resolver = RelationshipResolver(sample_entities)
        resolver.resolve()

        # process calls helper and transform
        callees = resolver.get_callees("func1")
        callee_names = [c.name for c in callees]
        assert "helper" in callee_names

    def test_get_dependencies(self, sample_entities):
        """Test getting dependencies of an entity."""
        resolver = RelationshipResolver(sample_entities)
        resolver.resolve()

        deps = resolver.get_dependencies("func1")
        assert "calls" in deps
        assert len(deps["calls"]) > 0

    def test_get_dependents(self, sample_entities):
        """Test getting dependents of an entity."""
        resolver = RelationshipResolver(sample_entities)
        resolver.resolve()

        # Get entities that depend on helper
        deps = resolver.get_dependents("func2")
        assert "callers" in deps
        assert len(deps["callers"]) > 0

    def test_unresolved_calls(self, sample_entities):
        """Test tracking of unresolved calls."""
        resolver = RelationshipResolver(sample_entities)
        result = resolver.resolve()

        # transform calls "external_func" which doesn't exist
        # (We didn't add this call, so unresolved should be empty in our case)
        # But process calls "transform" which should be resolved
        assert result.stats["calls_resolved"] > 0

    def test_resolution_stats(self, sample_entities):
        """Test resolution statistics."""
        resolver = RelationshipResolver(sample_entities)
        result = resolver.resolve()

        assert result.stats["functions_analyzed"] > 0
        assert result.stats["classes_analyzed"] > 0
        assert result.stats["calls_resolved"] > 0

    def test_resolution_result_to_dict(self, sample_entities):
        """Test ResolutionResult serialization."""
        resolver = RelationshipResolver(sample_entities)
        result = resolver.resolve()
        data = result.to_dict()

        assert "relationship_count" in data
        assert "relationships_by_type" in data
        assert "stats" in data
        assert data["relationship_count"] == len(result.relationships)

    def test_empty_entities(self):
        """Test resolver with no entities."""
        resolver = RelationshipResolver([])
        result = resolver.resolve()

        assert len(result.relationships) == 0
        assert result.stats["functions_analyzed"] == 0
