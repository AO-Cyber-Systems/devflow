"""Tests for code models."""

import pytest
from datetime import datetime

from devflow.code.models import (
    CodeEntity,
    CodeEntityType,
    CodeRelationType,
    FunctionEntity,
    ClassEntity,
    ImportEntity,
    ModuleEntity,
    Parameter,
    Property,
)


class TestCodeEntityType:
    """Tests for CodeEntityType enum."""

    def test_display_names(self):
        """Test that all entity types have display names."""
        for entity_type in CodeEntityType:
            assert entity_type.display_name
            assert isinstance(entity_type.display_name, str)

    def test_icons(self):
        """Test that all entity types have icons."""
        for entity_type in CodeEntityType:
            assert entity_type.icon
            assert isinstance(entity_type.icon, str)


class TestCodeRelationType:
    """Tests for CodeRelationType enum."""

    def test_display_names(self):
        """Test that all relationship types have display names."""
        for rel_type in CodeRelationType:
            assert rel_type.display_name
            assert isinstance(rel_type.display_name, str)

    def test_inverse_relationships(self):
        """Test inverse relationship mapping."""
        assert CodeRelationType.CALLS.inverse == CodeRelationType.CALLED_BY
        assert CodeRelationType.CALLED_BY.inverse == CodeRelationType.CALLS


class TestParameter:
    """Tests for Parameter dataclass."""

    def test_basic_parameter(self):
        """Test basic parameter creation."""
        param = Parameter(name="arg")
        assert param.name == "arg"
        assert param.type_annotation is None
        assert param.default_value is None
        assert not param.is_variadic
        assert not param.is_keyword

    def test_typed_parameter(self):
        """Test parameter with type annotation."""
        param = Parameter(name="value", type_annotation="int", default_value="0")
        assert str(param) == "value: int = 0"

    def test_variadic_parameter(self):
        """Test *args parameter."""
        param = Parameter(name="args", is_variadic=True)
        assert str(param) == "*args"

    def test_keyword_parameter(self):
        """Test **kwargs parameter."""
        param = Parameter(name="kwargs", is_keyword=True)
        assert str(param) == "**kwargs"

    def test_serialization(self):
        """Test to_dict and from_dict."""
        param = Parameter(name="x", type_annotation="int", default_value="10")
        data = param.to_dict()
        restored = Parameter.from_dict(data)
        assert restored.name == param.name
        assert restored.type_annotation == param.type_annotation
        assert restored.default_value == param.default_value


class TestProperty:
    """Tests for Property dataclass."""

    def test_basic_property(self):
        """Test basic property creation."""
        prop = Property(name="value")
        assert prop.name == "value"
        assert prop.type_annotation is None

    def test_typed_property(self):
        """Test property with type annotation."""
        prop = Property(name="count", type_annotation="int", default_value="0")
        assert prop.name == "count"
        assert prop.type_annotation == "int"
        assert prop.default_value == "0"

    def test_serialization(self):
        """Test to_dict and from_dict."""
        prop = Property(name="x", type_annotation="str", is_class_var=True)
        data = prop.to_dict()
        restored = Property.from_dict(data)
        assert restored.name == prop.name
        assert restored.is_class_var == prop.is_class_var


class TestCodeEntity:
    """Tests for CodeEntity base class."""

    def test_generate_id(self):
        """Test ID generation."""
        id1 = CodeEntity.generate_id("file.py", 10, "func")
        id2 = CodeEntity.generate_id("file.py", 10, "func")
        id3 = CodeEntity.generate_id("file.py", 11, "func")

        # Same inputs should produce same ID
        assert id1 == id2
        # Different inputs should produce different ID
        assert id1 != id3

    def test_serialization(self):
        """Test to_dict and from_dict."""
        entity = CodeEntity(
            id="test123",
            name="test",
            qualified_name="module.test",
            entity_type=CodeEntityType.FUNCTION,
            file_path="/path/to/file.py",
            line_start=1,
            line_end=10,
            language="python",
            source_code="def test(): pass",
            docstring="Test function",
            tags=["test"],
        )

        data = entity.to_dict()
        assert data["name"] == "test"
        assert data["entity_type"] == "function"

        restored = CodeEntity.from_dict(data)
        assert restored.name == entity.name
        assert restored.qualified_name == entity.qualified_name


class TestFunctionEntity:
    """Tests for FunctionEntity."""

    def test_basic_function(self):
        """Test basic function entity."""
        func = FunctionEntity(
            id="func1",
            name="process",
            qualified_name="module.process",
            entity_type=CodeEntityType.FUNCTION,
            file_path="/path/file.py",
            line_start=1,
            line_end=5,
            language="python",
            source_code="def process(): pass",
        )
        assert func.name == "process"
        assert not func.is_async
        assert not func.is_method

    def test_async_function(self):
        """Test async function entity."""
        func = FunctionEntity(
            id="func1",
            name="fetch",
            qualified_name="module.fetch",
            entity_type=CodeEntityType.FUNCTION,
            file_path="/path/file.py",
            line_start=1,
            line_end=5,
            language="python",
            source_code="async def fetch(): pass",
            is_async=True,
            return_type="Awaitable[str]",
        )
        assert func.is_async
        assert "async" in func.signature

    def test_method_entity(self):
        """Test method entity."""
        method = FunctionEntity(
            id="method1",
            name="run",
            qualified_name="module.MyClass.run",
            entity_type=CodeEntityType.FUNCTION,
            file_path="/path/file.py",
            line_start=10,
            line_end=15,
            language="python",
            source_code="def run(self): pass",
            is_method=True,
            parent_class="module.MyClass",
        )
        # Entity type should be METHOD for methods
        assert method.entity_type == CodeEntityType.METHOD

    def test_signature_generation(self):
        """Test function signature generation."""
        func = FunctionEntity(
            id="func1",
            name="add",
            qualified_name="math.add",
            entity_type=CodeEntityType.FUNCTION,
            file_path="/path/file.py",
            line_start=1,
            line_end=5,
            language="python",
            source_code="def add(a, b): return a + b",
            parameters=[
                Parameter(name="a", type_annotation="int"),
                Parameter(name="b", type_annotation="int"),
            ],
            return_type="int",
        )
        sig = func.signature
        assert "add" in sig
        assert "a: int" in sig
        assert "b: int" in sig
        assert "-> int" in sig

    def test_serialization(self):
        """Test to_dict and from_dict."""
        func = FunctionEntity(
            id="func1",
            name="test",
            qualified_name="module.test",
            entity_type=CodeEntityType.FUNCTION,
            file_path="/path/file.py",
            line_start=1,
            line_end=5,
            language="python",
            source_code="def test(): pass",
            parameters=[Parameter(name="x", type_annotation="int")],
            return_type="bool",
            is_async=True,
            calls=["helper"],
        )

        data = func.to_dict()
        assert data["is_async"]
        assert len(data["parameters"]) == 1
        assert data["calls"] == ["helper"]

        restored = FunctionEntity.from_dict(data)
        assert restored.is_async == func.is_async
        assert len(restored.parameters) == len(func.parameters)


class TestClassEntity:
    """Tests for ClassEntity."""

    def test_basic_class(self):
        """Test basic class entity."""
        cls = ClassEntity(
            id="cls1",
            name="MyClass",
            qualified_name="module.MyClass",
            entity_type=CodeEntityType.CLASS,
            file_path="/path/file.py",
            line_start=1,
            line_end=20,
            language="python",
            source_code="class MyClass: pass",
        )
        assert cls.name == "MyClass"
        assert not cls.is_abstract
        assert not cls.is_dataclass

    def test_class_with_inheritance(self):
        """Test class with base classes."""
        cls = ClassEntity(
            id="cls1",
            name="Child",
            qualified_name="module.Child",
            entity_type=CodeEntityType.CLASS,
            file_path="/path/file.py",
            line_start=1,
            line_end=20,
            language="python",
            source_code="class Child(Parent): pass",
            base_classes=["Parent"],
        )
        assert "Parent" in cls.base_classes

    def test_dataclass(self):
        """Test dataclass entity."""
        cls = ClassEntity(
            id="cls1",
            name="Data",
            qualified_name="module.Data",
            entity_type=CodeEntityType.CLASS,
            file_path="/path/file.py",
            line_start=1,
            line_end=10,
            language="python",
            source_code="@dataclass\nclass Data: pass",
            decorators=["dataclass"],
            is_dataclass=True,
            properties=[
                Property(name="value", type_annotation="int"),
            ],
        )
        assert cls.is_dataclass
        assert len(cls.properties) == 1

    def test_serialization(self):
        """Test to_dict and from_dict."""
        cls = ClassEntity(
            id="cls1",
            name="Test",
            qualified_name="module.Test",
            entity_type=CodeEntityType.CLASS,
            file_path="/path/file.py",
            line_start=1,
            line_end=20,
            language="python",
            source_code="class Test: pass",
            base_classes=["Base"],
            methods=["module.Test.run"],
        )

        data = cls.to_dict()
        assert "Base" in data["base_classes"]

        restored = ClassEntity.from_dict(data)
        assert restored.base_classes == cls.base_classes
        assert restored.methods == cls.methods


class TestImportEntity:
    """Tests for ImportEntity."""

    def test_simple_import(self):
        """Test simple import statement."""
        imp = ImportEntity(
            id="imp1",
            name="import os",
            qualified_name="import:os:",
            entity_type=CodeEntityType.IMPORT,
            file_path="/path/file.py",
            line_start=1,
            line_end=1,
            language="python",
            source_code="import os",
            module="os",
            names=["os"],
        )
        assert imp.module == "os"
        assert not imp.is_relative

    def test_from_import(self):
        """Test from import statement."""
        imp = ImportEntity(
            id="imp1",
            name="from typing import List",
            qualified_name="import:typing:List",
            entity_type=CodeEntityType.IMPORT,
            file_path="/path/file.py",
            line_start=1,
            line_end=1,
            language="python",
            source_code="from typing import List",
            module="typing",
            names=["List"],
        )
        assert imp.module == "typing"
        assert "List" in imp.names

    def test_relative_import(self):
        """Test relative import statement."""
        imp = ImportEntity(
            id="imp1",
            name="from . import utils",
            qualified_name="import:.utils",
            entity_type=CodeEntityType.IMPORT,
            file_path="/path/file.py",
            line_start=1,
            line_end=1,
            language="python",
            source_code="from . import utils",
            module="",
            names=["utils"],
            is_relative=True,
            level=1,
        )
        assert imp.is_relative
        assert imp.level == 1


class TestModuleEntity:
    """Tests for ModuleEntity."""

    def test_basic_module(self):
        """Test basic module entity."""
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
            docstring="Utility functions",
        )
        assert mod.name == "utils"
        assert not mod.is_package
        assert not mod.is_init

    def test_package_init(self):
        """Test package __init__ module."""
        mod = ModuleEntity(
            id="mod1",
            name="mypackage",
            qualified_name="mypackage",
            entity_type=CodeEntityType.MODULE,
            file_path="/path/mypackage/__init__.py",
            line_start=1,
            line_end=50,
            language="python",
            source_code="",
            is_package=True,
            is_init=True,
            exports=["func1", "Class1"],
        )
        assert mod.is_package
        assert mod.is_init
        assert "func1" in mod.exports
